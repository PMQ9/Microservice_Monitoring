from flask import Flask, jsonify
import random
import time
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)

# Initialize OpenTelemetry
metrics.set_meter_provider(MeterProvider())
metrics.get_meter_provider().shutdown()  # Clear default meter
meter = metrics.get_meter("backend-service")

# Create multiple metrics for better visualization
request_counter = meter.create_counter("http.requests", description="Total HTTP requests")
api_counter = meter.create_counter("api.calls", description="API endpoint calls")
error_counter = meter.create_counter("api.errors", description="API errors")
latency_histogram = meter.create_histogram("api.latency.ms", description="API latency in milliseconds")
active_users = meter.create_up_down_counter("users.active", description="Active users")
data_processed = meter.create_counter("data.processed.bytes", description="Data processed in bytes")

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("backend-service")
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger.monitoring.svc.cluster.local:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
metrics.set_meter_provider(MeterProvider(metric_readers=[PrometheusMetricReader()]))

FlaskInstrumentor().instrument_app(app)

@app.route('/api', methods=['GET'])
def get_message():
    request_counter.add(1)
    api_counter.add(1)
    start_time = time.time()

    with tracer.start_as_current_span("backend-api"):
        data_processed.add(256)
        latency = (time.time() - start_time) * 1000
        latency_histogram.record(latency)
        return jsonify({"message": "Hello from backend!", "status": "success"})

@app.route('/api/users', methods=['GET'])
def get_users():
    request_counter.add(1)
    api_counter.add(1)
    start_time = time.time()

    with tracer.start_as_current_span("get-users"):
        users = [
            {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
            {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
            {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com"},
        ]
        data_processed.add(len(users) * 100)
        latency = (time.time() - start_time) * 1000
        latency_histogram.record(latency)
        return jsonify({"users": users, "count": len(users)})

@app.route('/api/data', methods=['GET'])
def get_data():
    request_counter.add(1)
    api_counter.add(1)
    start_time = time.time()

    with tracer.start_as_current_span("get-data"):
        # Generate random data to simulate processing
        data = [random.randint(1, 100) for _ in range(10)]
        data_processed.add(len(data) * 50)
        latency = (time.time() - start_time) * 1000
        latency_histogram.record(latency)
        return jsonify({"data": data, "count": len(data)})

@app.route('/api/process', methods=['GET'])
def process_data():
    request_counter.add(1)
    api_counter.add(1)
    start_time = time.time()

    with tracer.start_as_current_span("process-data"):
        # Simulate processing time
        time.sleep(random.uniform(0.1, 0.5))

        # Randomly simulate occasional errors for monitoring
        if random.random() < 0.1:
            error_counter.add(1)
            latency = (time.time() - start_time) * 1000
            latency_histogram.record(latency)
            return jsonify({"error": "Processing failed", "status": "error"}), 500

        data_processed.add(512)
        latency = (time.time() - start_time) * 1000
        latency_histogram.record(latency)
        return jsonify({"status": "processed", "result": random.randint(100, 999)})

@app.route('/api/health', methods=['GET'])
def health_check():
    request_counter.add(1)
    with tracer.start_as_current_span("health-check"):
        return jsonify({"status": "healthy", "service": "backend"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
