from flask import Flask, jsonify, request
import logging
import random
import time
from datetime import datetime
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from prometheus_client import start_http_server

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenTelemetry Tracing Setup
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("content-creator-service")
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger.monitoring.svc.cluster.local:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# OpenTelemetry Metrics Setup
start_http_server(port=8000, addr="0.0.0.0")
reader = PrometheusMetricReader()
metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
meter = metrics.get_meter("content-creator-service")

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Custom Metrics
content_created_counter = meter.create_counter(
    "content.created",
    description="Total number of content items created"
)
active_creators_gauge = meter.create_up_down_counter(
    "creators.active",
    description="Number of active content creators"
)
content_creation_duration = meter.create_histogram(
    "content.creation.duration",
    description="Content creation duration in seconds"
)
creator_requests_counter = meter.create_counter(
    "creator.requests.total",
    description="Total number of requests to creator service"
)

# In-memory storage
content_creators = {}
content_items = {}
creator_id_counter = 1
content_id_counter = 1

# Content types
CONTENT_TYPES = ["video", "image", "article", "audio", "story"]

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "content-creator"}), 200

@app.route('/api/creators', methods=['POST'])
def create_creator():
    """Register a new content creator"""
    global creator_id_counter

    with tracer.start_as_current_span("create_creator") as span:
        creator_requests_counter.add(1, {"endpoint": "/api/creators", "method": "POST"})

        data = request.get_json() or {}
        creator_name = data.get('name', f'Creator_{creator_id_counter}')

        creator_id = f'creator_{creator_id_counter}'
        creator_id_counter += 1

        content_creators[creator_id] = {
            'id': creator_id,
            'name': creator_name,
            'created_at': datetime.now().isoformat(),
            'total_content': 0,
            'followers': random.randint(100, 100000)
        }

        active_creators_gauge.add(1)
        span.set_attribute("creator.id", creator_id)
        span.set_attribute("creator.name", creator_name)

        logger.info(f"Created new creator: {creator_id} - {creator_name}")

        return jsonify(content_creators[creator_id]), 201

@app.route('/api/creators', methods=['GET'])
def get_creators():
    """Get all content creators"""
    with tracer.start_as_current_span("get_creators"):
        creator_requests_counter.add(1, {"endpoint": "/api/creators", "method": "GET"})
        return jsonify({
            'total': len(content_creators),
            'creators': list(content_creators.values())
        }), 200

@app.route('/api/creators/<creator_id>', methods=['GET'])
def get_creator(creator_id):
    """Get specific creator details"""
    with tracer.start_as_current_span("get_creator") as span:
        creator_requests_counter.add(1, {"endpoint": "/api/creators/:id", "method": "GET"})
        span.set_attribute("creator.id", creator_id)

        if creator_id not in content_creators:
            return jsonify({'error': 'Creator not found'}), 404

        return jsonify(content_creators[creator_id]), 200

@app.route('/api/content', methods=['POST'])
def create_content():
    """Create new content"""
    global content_id_counter

    with tracer.start_as_current_span("create_content") as span:
        start_time = time.time()
        creator_requests_counter.add(1, {"endpoint": "/api/content", "method": "POST"})

        data = request.get_json() or {}
        creator_id = data.get('creator_id')

        if not creator_id or creator_id not in content_creators:
            return jsonify({'error': 'Invalid creator_id'}), 400

        # Simulate content creation time
        creation_delay = random.uniform(0.1, 0.5)
        time.sleep(creation_delay)

        content_type = data.get('type', random.choice(CONTENT_TYPES))
        content_id = f'content_{content_id_counter}'
        content_id_counter += 1

        content_items[content_id] = {
            'id': content_id,
            'creator_id': creator_id,
            'type': content_type,
            'title': data.get('title', f'Content {content_id}'),
            'created_at': datetime.now().isoformat(),
            'views': 0,
            'likes': 0
        }

        # Update creator stats
        content_creators[creator_id]['total_content'] += 1

        # Record metrics
        content_created_counter.add(1, {
            "content.type": content_type,
            "creator.id": creator_id
        })

        duration = time.time() - start_time
        content_creation_duration.record(duration, {"content.type": content_type})

        span.set_attribute("content.id", content_id)
        span.set_attribute("content.type", content_type)
        span.set_attribute("creator.id", creator_id)

        logger.info(f"Content created: {content_id} by {creator_id} (type: {content_type})")

        return jsonify(content_items[content_id]), 201

@app.route('/api/content', methods=['GET'])
def get_content():
    """Get all content"""
    with tracer.start_as_current_span("get_content"):
        creator_requests_counter.add(1, {"endpoint": "/api/content", "method": "GET"})
        return jsonify({
            'total': len(content_items),
            'content': list(content_items.values())
        }), 200

@app.route('/api/content/<content_id>', methods=['GET'])
def get_content_item(content_id):
    """Get specific content item"""
    with tracer.start_as_current_span("get_content_item") as span:
        creator_requests_counter.add(1, {"endpoint": "/api/content/:id", "method": "GET"})
        span.set_attribute("content.id", content_id)

        if content_id not in content_items:
            return jsonify({'error': 'Content not found'}), 404

        return jsonify(content_items[content_id]), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    with tracer.start_as_current_span("get_stats"):
        creator_requests_counter.add(1, {"endpoint": "/api/stats", "method": "GET"})

        content_by_type = {}
        for content in content_items.values():
            content_type = content['type']
            content_by_type[content_type] = content_by_type.get(content_type, 0) + 1

        return jsonify({
            'total_creators': len(content_creators),
            'total_content': len(content_items),
            'content_by_type': content_by_type
        }), 200

if __name__ == '__main__':
    logger.info("Starting Content Creator Service on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
