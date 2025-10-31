from flask import Flask, jsonify, request
import logging
import random
import time
import requests
import threading
from datetime import datetime
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from prometheus_client import start_http_server

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenTelemetry Tracing Setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("content-service")
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger.monitoring.svc.cluster.local:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# OpenTelemetry Metrics Setup
start_http_server(port=8000, addr="0.0.0.0")
reader = PrometheusMetricReader()
metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
meter = metrics.get_meter("content-service")

# Instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Custom Metrics
traffic_generation_counter = meter.create_counter(
    "traffic.generated",
    description="Total traffic generation events"
)
simulation_active_gauge = meter.create_up_down_counter(
    "simulation.active",
    description="Whether simulation is active"
)

# Service URLs
CONTENT_CREATOR_SERVICE = "http://content-creator-service:5001"
USER_SERVICE = "http://user-service:5002"

# Simulation state
simulation_running = False
simulation_thread = None

def generate_random_traffic():
    """Generate random traffic to simulate social media activity"""
    global simulation_running

    logger.info("Traffic generation started")
    simulation_active_gauge.add(1)

    creators = []
    users = []
    content_ids = []

    while simulation_running:
        try:
            with tracer.start_as_current_span("traffic_generation_cycle"):
                # Randomly decide what action to take
                action = random.choices(
                    ['create_creator', 'create_user', 'create_content', 'view_content', 'like_content'],
                    weights=[5, 10, 15, 50, 20],
                    k=1
                )[0]

                if action == 'create_creator':
                    # Create a new content creator
                    response = requests.post(
                        f"{CONTENT_CREATOR_SERVICE}/api/creators",
                        json={'name': f'Creator_{random.randint(1000, 9999)}'},
                        timeout=5
                    )
                    if response.status_code == 201:
                        creator = response.json()
                        creators.append(creator['id'])
                        logger.info(f"Created creator: {creator['id']}")
                        traffic_generation_counter.add(1, {"action": "create_creator"})

                elif action == 'create_user':
                    # Create a new user
                    response = requests.post(
                        f"{USER_SERVICE}/api/users",
                        json={'username': f'User_{random.randint(1000, 9999)}'},
                        timeout=5
                    )
                    if response.status_code == 201:
                        user = response.json()
                        users.append(user['id'])
                        logger.info(f"Created user: {user['id']}")
                        traffic_generation_counter.add(1, {"action": "create_user"})

                elif action == 'create_content' and creators:
                    # Create content from a random creator
                    creator_id = random.choice(creators)
                    content_types = ['video', 'image', 'article', 'audio', 'story']
                    response = requests.post(
                        f"{CONTENT_CREATOR_SERVICE}/api/content",
                        json={
                            'creator_id': creator_id,
                            'type': random.choice(content_types),
                            'title': f'Content {random.randint(1000, 9999)}'
                        },
                        timeout=5
                    )
                    if response.status_code == 201:
                        content = response.json()
                        content_ids.append(content['id'])
                        logger.info(f"Created content: {content['id']} by {creator_id}")
                        traffic_generation_counter.add(1, {"action": "create_content"})

                elif action == 'view_content' and users and content_ids:
                    # Random user views random content
                    user_id = random.choice(users)
                    content_id = random.choice(content_ids)
                    response = requests.post(
                        f"{USER_SERVICE}/api/users/{user_id}/view/{content_id}",
                        timeout=10
                    )
                    if response.status_code == 200:
                        logger.info(f"User {user_id} viewed content {content_id}")
                        traffic_generation_counter.add(1, {"action": "view_content"})

                elif action == 'like_content' and users and content_ids:
                    # Random user likes random content
                    user_id = random.choice(users)
                    content_id = random.choice(content_ids)
                    response = requests.post(
                        f"{USER_SERVICE}/api/users/{user_id}/like/{content_id}",
                        timeout=5
                    )
                    if response.status_code == 200:
                        logger.info(f"User {user_id} liked content {content_id}")
                        traffic_generation_counter.add(1, {"action": "like_content"})

        except Exception as e:
            logger.error(f"Error during traffic generation: {e}")

        # Random delay between actions (0.5 to 2 seconds)
        time.sleep(random.uniform(0.5, 2.0))

    simulation_active_gauge.add(-1)
    logger.info("Traffic generation stopped")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "content-service"}), 200

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    """Start the traffic generation simulation"""
    global simulation_running, simulation_thread

    with tracer.start_as_current_span("start_simulation"):
        if simulation_running:
            return jsonify({'message': 'Simulation already running'}), 200

        simulation_running = True
        simulation_thread = threading.Thread(target=generate_random_traffic, daemon=True)
        simulation_thread.start()

        logger.info("Simulation started")
        return jsonify({'message': 'Simulation started'}), 200

@app.route('/api/simulation/stop', methods=['POST'])
def stop_simulation():
    """Stop the traffic generation simulation"""
    global simulation_running

    with tracer.start_as_current_span("stop_simulation"):
        if not simulation_running:
            return jsonify({'message': 'Simulation not running'}), 200

        simulation_running = False
        logger.info("Simulation stop requested")

        return jsonify({'message': 'Simulation stopped'}), 200

@app.route('/api/simulation/status', methods=['GET'])
def simulation_status():
    """Get simulation status"""
    with tracer.start_as_current_span("simulation_status"):
        return jsonify({
            'running': simulation_running,
            'timestamp': datetime.now().isoformat()
        }), 200

@app.route('/api/platform/stats', methods=['GET'])
def platform_stats():
    """Get aggregated platform statistics"""
    with tracer.start_as_current_span("platform_stats"):
        try:
            # Get creator stats
            creator_response = requests.get(f"{CONTENT_CREATOR_SERVICE}/api/stats", timeout=5)
            creator_stats = creator_response.json() if creator_response.status_code == 200 else {}

            # Get user stats
            user_response = requests.get(f"{USER_SERVICE}/api/stats", timeout=5)
            user_stats = user_response.json() if user_response.status_code == 200 else {}

            return jsonify({
                'creator_stats': creator_stats,
                'user_stats': user_stats,
                'simulation_running': simulation_running,
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            logger.error(f"Error fetching platform stats: {e}")
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Content Service on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=False)
