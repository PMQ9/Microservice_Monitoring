#!/bin/bash

# Deploy Scaled Social Media Application
# This script deploys the complete infrastructure with PostgreSQL, Redis, and scaled services

set -e

echo "===================================="
echo "🚀 DEPLOYING SCALED SOCIAL MEDIA APP"
echo "===================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Deploy PostgreSQL
echo -e "\n${BLUE}📦 Step 1: Deploying PostgreSQL database...${NC}"
kubectl apply -f app/database/postgres-deployment.yaml
echo -e "${GREEN}✓ PostgreSQL deployment created${NC}"

# Step 2: Deploy Redis
echo -e "\n${BLUE}📦 Step 2: Deploying Redis cache...${NC}"
kubectl apply -f app/database/redis-deployment.yaml
echo -e "${GREEN}✓ Redis deployment created${NC}"

# Step 3: Wait for database to be ready
echo -e "\n${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n default --timeout=120s
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"

echo -e "\n${YELLOW}⏳ Waiting for Redis to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=redis -n default --timeout=120s
echo -e "${GREEN}✓ Redis is ready${NC}"

# Step 4: Initialize database schema
echo -e "\n${BLUE}🗄️  Step 3: Initializing database schema...${NC}"
POSTGRES_POD=$(kubectl get pod -l app=postgres -n default -o jsonpath='{.items[0].metadata.name}')
kubectl cp app/database/init-db.sql default/$POSTGRES_POD:/tmp/init-db.sql
kubectl exec -n default $POSTGRES_POD -- psql -U socialmedia -d socialmedia -f /tmp/init-db.sql
echo -e "${GREEN}✓ Database schema initialized${NC}"

# Step 5: Build updated Docker images
echo -e "\n${BLUE}🐳 Step 4: Building updated Docker images...${NC}"
eval $(minikube docker-env)

echo "  Building content-creator service..."
cd app/content-creator && docker build -t content-creator-service:latest . && cd ../..
echo -e "${GREEN}  ✓ content-creator service built${NC}"

echo "  Building user-service..."
cd app/user-service && docker build -t user-service:latest . && cd ../..
echo -e "${GREEN}  ✓ user-service built${NC}"

echo "  Building content-service..."
cd app/content-service && docker build -t content-service:latest . && cd ../..
echo -e "${GREEN}  ✓ content-service built${NC}"

# Step 6: Deploy services
echo -e "\n${BLUE}🚀 Step 5: Deploying microservices...${NC}"
kubectl apply -f app/content-creator/content-creator-deployment.yaml
kubectl apply -f app/content-creator/content-creator-service.yaml
echo -e "${GREEN}  ✓ Content Creator service deployed${NC}"

kubectl apply -f app/user-service/user-service-deployment.yaml
kubectl apply -f app/user-service/user-service-service.yaml
echo -e "${GREEN}  ✓ User service deployed${NC}"

kubectl apply -f app/content-service/content-service-deployment.yaml
kubectl apply -f app/content-service/content-service-service.yaml
echo -e "${GREEN}  ✓ Content service deployed${NC}"

# Step 7: Wait for services to be ready
echo -e "\n${YELLOW}⏳ Waiting for services to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=content-creator -n default --timeout=120s
kubectl wait --for=condition=ready pod -l app=user-service -n default --timeout=120s
kubectl wait --for=condition=ready pod -l app=content-service -n default --timeout=120s
echo -e "${GREEN}✓ All services are ready${NC}"

# Step 8: Generate scaled data
echo -e "\n${BLUE}📊 Step 6: Generating scaled data...${NC}"
echo -e "${YELLOW}This may take several minutes. Deploying data generation job...${NC}"

# Create a Kubernetes job to run data generation
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-gen-script
  namespace: default
data:
  generate-data.py: |
$(cat utils/generate-scaled-data.py | sed 's/^/    /')
---
apiVersion: batch/v1
kind: Job
metadata:
  name: data-generation-job
  namespace: default
spec:
  ttlSecondsAfterFinished: 300
  template:
    spec:
      containers:
      - name: data-generator
        image: python:3.9-slim
        command: ["/bin/bash", "-c"]
        args:
          - |
            pip install psycopg2-binary faker
            echo | python /scripts/generate-data.py
        volumeMounts:
        - name: script
          mountPath: /scripts
      volumes:
      - name: script
        configMap:
          name: data-gen-script
      restartPolicy: Never
  backoffLimit: 2
EOF

echo -e "${GREEN}✓ Data generation job created${NC}"
echo -e "${YELLOW}Monitoring data generation progress...${NC}"

# Wait for job to complete
kubectl wait --for=condition=complete job/data-generation-job -n default --timeout=600s || true

# Show job logs
echo -e "\n${BLUE}📋 Data Generation Logs:${NC}"
kubectl logs job/data-generation-job -n default

# Step 9: Apply ServiceMonitor for Prometheus
echo -e "\n${BLUE}📈 Step 7: Configuring Prometheus monitoring...${NC}"
if kubectl get crd servicemonitors.monitoring.coreos.com &> /dev/null; then
    kubectl apply -f observability/prometheus/service-monitor.yaml
    echo -e "${GREEN}✓ ServiceMonitor configured${NC}"
else
    echo -e "${YELLOW}⚠ ServiceMonitor CRD not found. Skipping...${NC}"
fi

# Step 10: Summary
echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}=====================================${NC}"

echo -e "\n${BLUE}📊 Deployed Components:${NC}"
echo "  • PostgreSQL database (persistent storage)"
echo "  • Redis cache (performance optimization)"
echo "  • Content Creator Service (enhanced with DB)"
echo "  • User Service (enhanced with DB)"
echo "  • Content Service (traffic simulation)"

echo -e "\n${BLUE}📈 Scaled Data:${NC}"
kubectl exec -n default $POSTGRES_POD -- psql -U socialmedia -d socialmedia -c "
    SELECT
        'Creators' as type, COUNT(*)::text as count FROM content_creators
    UNION ALL
    SELECT 'Users', COUNT(*)::text FROM users
    UNION ALL
    SELECT 'Content Items', COUNT(*)::text FROM content_items
    UNION ALL
    SELECT 'Activities', COUNT(*)::text FROM user_activities
    UNION ALL
    SELECT 'Follows', COUNT(*)::text FROM user_follows;
" -t

echo -e "\n${BLUE}🔗 Access Services:${NC}"
echo "  Content Service UI:"
echo "    minikube service content-service -n default --url"
echo ""
echo "  Grafana Dashboard:"
echo "    minikube service grafana -n monitoring --url"
echo ""
echo "  Jaeger Tracing:"
echo "    minikube service jaeger -n monitoring --url"
echo ""

echo -e "\n${BLUE}📊 View Metrics:${NC}"
echo "  Content Creator metrics:"
echo "    kubectl port-forward svc/content-creator-service 8001:8000 -n default"
echo "    curl http://localhost:8001/metrics"
echo ""

echo -e "\n${BLUE}🧪 Start Traffic Simulation:${NC}"
echo "  CONTENT_URL=\$(minikube service content-service -n default --url)"
echo "  curl -X POST \$CONTENT_URL/api/simulation/start"
echo ""

echo -e "${GREEN}Happy monitoring! 🎉${NC}"
