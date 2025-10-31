from flask import Flask, jsonify, request
import logging
import random
import time
import requests
from datetime import datetime
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
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
tracer = trace.get_tracer("user-service")
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger.monitoring.svc.cluster.local:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))

# OpenTelemetry Metrics Setup
start_http_server(port=8000, addr="0.0.0.0")
reader = PrometheusMetricReader()
metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
meter = metrics.get_meter("user-service")

# Instrument Flask and Requests
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Custom Metrics
active_users_gauge = meter.create_up_down_counter(
    "users.active",
    description="Number of active users"
)
content_views_counter = meter.create_counter(
    "content.views",
    description="Total number of content views by users"
)
content_likes_counter = meter.create_counter(
    "content.likes",
    description="Total number of content likes"
)
user_requests_counter = meter.create_counter(
    "user.requests.total",
    description="Total number of requests to user service"
)
content_access_duration = meter.create_histogram(
    "content.access.duration",
    description="Content access duration in seconds"
)
user_session_duration = meter.create_histogram(
    "user.session.duration",
    description="User session duration in seconds"
)

# In-memory storage
users = {}
user_id_counter = 1
user_activity = {}

# Content Creator Service URL
CONTENT_CREATOR_SERVICE = "http://content-creator-service:5001"

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "user-service"}), 200

@app.route('/api/users', methods=['POST'])
def create_user():
    """Register a new user"""
    global user_id_counter

    with tracer.start_as_current_span("create_user") as span:
        user_requests_counter.add(1, {"endpoint": "/api/users", "method": "POST"})

        data = request.get_json() or {}
        username = data.get('username', f'User_{user_id_counter}')

        user_id = f'user_{user_id_counter}'
        user_id_counter += 1

        users[user_id] = {
            'id': user_id,
            'username': username,
            'created_at': datetime.now().isoformat(),
            'total_views': 0,
            'total_likes': 0,
            'session_start': datetime.now().isoformat()
        }

        user_activity[user_id] = {
            'viewed_content': [],
            'liked_content': [],
            'favorite_creators': []
        }

        active_users_gauge.add(1)
        span.set_attribute("user.id", user_id)
        span.set_attribute("user.username", username)

        logger.info(f"Created new user: {user_id} - {username}")

        return jsonify(users[user_id]), 201

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    with tracer.start_as_current_span("get_users"):
        user_requests_counter.add(1, {"endpoint": "/api/users", "method": "GET"})
        return jsonify({
            'total': len(users),
            'users': list(users.values())
        }), 200

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user details"""
    with tracer.start_as_current_span("get_user") as span:
        user_requests_counter.add(1, {"endpoint": "/api/users/:id", "method": "GET"})
        span.set_attribute("user.id", user_id)

        if user_id not in users:
            return jsonify({'error': 'User not found'}), 404

        user_data = users[user_id].copy()
        user_data['activity'] = user_activity.get(user_id, {})

        return jsonify(user_data), 200

@app.route('/api/users/<user_id>/view/<content_id>', methods=['POST'])
def view_content(user_id, content_id):
    """User views content"""
    with tracer.start_as_current_span("view_content") as span:
        start_time = time.time()
        user_requests_counter.add(1, {"endpoint": "/api/users/:id/view/:content_id", "method": "POST"})

        if user_id not in users:
            return jsonify({'error': 'User not found'}), 404

        span.set_attribute("user.id", user_id)
        span.set_attribute("content.id", content_id)

        # Simulate content viewing time
        view_duration = random.uniform(0.5, 3.0)
        time.sleep(view_duration)

        # Try to get content details from content-creator service
        try:
            response = requests.get(f"{CONTENT_CREATOR_SERVICE}/api/content/{content_id}", timeout=2)
            if response.status_code == 200:
                content_data = response.json()
                content_type = content_data.get('type', 'unknown')
                creator_id = content_data.get('creator_id', 'unknown')

                span.set_attribute("content.type", content_type)
                span.set_attribute("creator.id", creator_id)
            else:
                content_type = 'unknown'
                creator_id = 'unknown'
        except Exception as e:
            logger.error(f"Error fetching content details: {e}")
            content_type = 'unknown'
            creator_id = 'unknown'

        # Update user stats
        users[user_id]['total_views'] += 1
        if content_id not in user_activity[user_id]['viewed_content']:
            user_activity[user_id]['viewed_content'].append(content_id)

        # Record metrics
        content_views_counter.add(1, {
            "user.id": user_id,
            "content.id": content_id,
            "content.type": content_type
        })

        duration = time.time() - start_time
        content_access_duration.record(duration, {"content.type": content_type})

        logger.info(f"User {user_id} viewed content {content_id} (duration: {view_duration:.2f}s)")

        return jsonify({
            'user_id': user_id,
            'content_id': content_id,
            'view_duration': view_duration,
            'total_views': users[user_id]['total_views']
        }), 200

@app.route('/api/users/<user_id>/like/<content_id>', methods=['POST'])
def like_content(user_id, content_id):
    """User likes content"""
    with tracer.start_as_current_span("like_content") as span:
        user_requests_counter.add(1, {"endpoint": "/api/users/:id/like/:content_id", "method": "POST"})

        if user_id not in users:
            return jsonify({'error': 'User not found'}), 404

        span.set_attribute("user.id", user_id)
        span.set_attribute("content.id", content_id)

        # Try to get content details
        try:
            response = requests.get(f"{CONTENT_CREATOR_SERVICE}/api/content/{content_id}", timeout=2)
            if response.status_code == 200:
                content_data = response.json()
                content_type = content_data.get('type', 'unknown')
                span.set_attribute("content.type", content_type)
            else:
                content_type = 'unknown'
        except Exception as e:
            logger.error(f"Error fetching content details: {e}")
            content_type = 'unknown'

        # Update user stats
        users[user_id]['total_likes'] += 1
        if content_id not in user_activity[user_id]['liked_content']:
            user_activity[user_id]['liked_content'].append(content_id)

        # Record metrics
        content_likes_counter.add(1, {
            "user.id": user_id,
            "content.id": content_id,
            "content.type": content_type
        })

        logger.info(f"User {user_id} liked content {content_id}")

        return jsonify({
            'user_id': user_id,
            'content_id': content_id,
            'total_likes': users[user_id]['total_likes']
        }), 200

@app.route('/api/users/<user_id>/browse', methods=['POST'])
def browse_content(user_id):
    """User browses random content"""
    with tracer.start_as_current_span("browse_content") as span:
        user_requests_counter.add(1, {"endpoint": "/api/users/:id/browse", "method": "POST"})

        if user_id not in users:
            return jsonify({'error': 'User not found'}), 404

        span.set_attribute("user.id", user_id)

        # Get available content from content-creator service
        try:
            response = requests.get(f"{CONTENT_CREATOR_SERVICE}/api/content", timeout=2)
            if response.status_code == 200:
                content_data = response.json()
                available_content = content_data.get('content', [])

                if available_content:
                    # Randomly select content to view
                    selected_content = random.choice(available_content)
                    content_id = selected_content['id']

                    # View the content
                    view_response = requests.post(
                        f"http://localhost:5002/api/users/{user_id}/view/{content_id}",
                        timeout=5
                    )

                    # Maybe like it (30% chance)
                    if random.random() < 0.3:
                        requests.post(
                            f"http://localhost:5002/api/users/{user_id}/like/{content_id}",
                            timeout=2
                        )

                    return jsonify({
                        'user_id': user_id,
                        'content_viewed': selected_content
                    }), 200
                else:
                    return jsonify({'message': 'No content available'}), 200
            else:
                return jsonify({'error': 'Could not fetch content'}), 500
        except Exception as e:
            logger.error(f"Error browsing content: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall user statistics"""
    with tracer.start_as_current_span("get_stats"):
        user_requests_counter.add(1, {"endpoint": "/api/stats", "method": "GET"})

        total_views = sum(user['total_views'] for user in users.values())
        total_likes = sum(user['total_likes'] for user in users.values())

        return jsonify({
            'total_users': len(users),
            'total_views': total_views,
            'total_likes': total_likes,
            'avg_views_per_user': total_views / len(users) if users else 0,
            'avg_likes_per_user': total_likes / len(users) if users else 0
        }), 200

if __name__ == '__main__':
    logger.info("Starting User Service on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)
