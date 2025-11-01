from flask import Flask, jsonify, request
import logging
import random
import time
import os
import json
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
import psycopg2
from psycopg2 import pool
import redis

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'postgres-service')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'socialmedia')
DB_USER = os.getenv('DB_USER', 'socialmedia')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'socialmedia123')

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis-service')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# Initialize connection pools
db_pool = None
redis_client = None

def init_db_pool():
    """Initialize PostgreSQL connection pool"""
    global db_pool
    try:
        db_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=20,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info("Database connection pool created successfully")
    except Exception as e:
        logger.error(f"Failed to create database connection pool: {e}")
        db_pool = None

def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=5
        )
        redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None

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
db_query_duration = meter.create_histogram(
    "db.query.duration",
    description="Database query duration in seconds"
)
db_connection_pool_size = meter.create_up_down_counter(
    "db.connection.pool.size",
    description="Current database connection pool size"
)
cache_hit_counter = meter.create_counter(
    "cache.hits",
    description="Number of cache hits"
)
cache_miss_counter = meter.create_counter(
    "cache.misses",
    description="Number of cache misses"
)
db_error_counter = meter.create_counter(
    "db.errors",
    description="Number of database errors"
)

# Content types and categories
CONTENT_TYPES = ["video", "image", "article", "audio", "story"]
CREATOR_CATEGORIES = ["technology", "fitness", "food", "gaming", "music", "education", "entertainment", "travel"]

def get_db_connection():
    """Get a connection from the pool"""
    if db_pool:
        try:
            return db_pool.getconn()
        except Exception as e:
            logger.error(f"Failed to get database connection: {e}")
            db_error_counter.add(1, {"operation": "get_connection"})
    return None

def release_db_connection(conn):
    """Return connection to the pool"""
    if db_pool and conn:
        try:
            db_pool.putconn(conn)
        except Exception as e:
            logger.error(f"Failed to release database connection: {e}")

def execute_query(query, params=None, fetch=False):
    """Execute a database query with metrics"""
    start_time = time.time()
    conn = get_db_connection()

    if not conn:
        logger.warning("Database not available, using fallback mode")
        return None

    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall()
            cursor.close()
            duration = time.time() - start_time
            db_query_duration.record(duration, {"operation": "select"})
            return result
        else:
            conn.commit()
            cursor.close()
            duration = time.time() - start_time
            db_query_duration.record(duration, {"operation": "write"})
            return True
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        db_error_counter.add(1, {"operation": "query"})
        conn.rollback()
        return None
    finally:
        release_db_connection(conn)

def get_from_cache(key):
    """Get value from Redis cache"""
    if not redis_client:
        return None

    try:
        value = redis_client.get(key)
        if value:
            cache_hit_counter.add(1, {"key_type": key.split(':')[0]})
            return json.loads(value)
        else:
            cache_miss_counter.add(1, {"key_type": key.split(':')[0]})
            return None
    except Exception as e:
        logger.error(f"Cache get failed: {e}")
        return None

def set_in_cache(key, value, ttl=300):
    """Set value in Redis cache with TTL"""
    if not redis_client:
        return False

    try:
        redis_client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Cache set failed: {e}")
        return False

def invalidate_cache(pattern):
    """Invalidate cache keys matching pattern"""
    if not redis_client:
        return

    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "content-creator",
        "database": "disconnected",
        "cache": "disconnected"
    }

    # Check database
    if db_pool:
        try:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                release_db_connection(conn)
                health_status["database"] = "connected"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

    # Check Redis
    if redis_client:
        try:
            redis_client.ping()
            health_status["cache"] = "connected"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")

    return jsonify(health_status), 200

@app.route('/api/creators', methods=['POST'])
def create_creator():
    """Register a new content creator"""
    with tracer.start_as_current_span("create_creator") as span:
        creator_requests_counter.add(1, {"endpoint": "/api/creators", "method": "POST"})

        data = request.get_json() or {}
        creator_name = data.get('name', f'Creator_{random.randint(1000, 9999)}')
        bio = data.get('bio', f'Bio for {creator_name}')
        category = data.get('category', random.choice(CREATOR_CATEGORIES))
        followers = data.get('followers', random.randint(100, 100000))
        verified = data.get('verified', followers > 50000)

        creator_id = f'creator_{int(time.time() * 1000000) % 1000000}_{random.randint(100, 999)}'

        query = """
            INSERT INTO content_creators (creator_id, name, bio, followers, verified, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, creator_id, name, bio, created_at, total_content, followers, verified, category
        """

        result = execute_query(query, (creator_id, creator_name, bio, followers, verified, category), fetch=True)

        if result:
            row = result[0]
            creator_data = {
                'id': creator_id,
                'name': row[2],
                'bio': row[3],
                'created_at': row[4].isoformat(),
                'total_content': row[5],
                'followers': row[6],
                'verified': row[7],
                'category': row[8]
            }

            active_creators_gauge.add(1)
            span.set_attribute("creator.id", creator_id)
            span.set_attribute("creator.name", creator_name)
            span.set_attribute("creator.category", category)

            # Invalidate stats cache
            invalidate_cache("stats:*")

            logger.info(f"Created new creator: {creator_id} - {creator_name} ({category})")
            return jsonify(creator_data), 201
        else:
            return jsonify({'error': 'Failed to create creator'}), 500

@app.route('/api/creators', methods=['GET'])
def get_creators():
    """Get all content creators with pagination"""
    with tracer.start_as_current_span("get_creators"):
        creator_requests_counter.add(1, {"endpoint": "/api/creators", "method": "GET"})

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        category = request.args.get('category')

        cache_key = f"creators:page:{page}:per_page:{per_page}:category:{category}"
        cached_data = get_from_cache(cache_key)

        if cached_data:
            return jsonify(cached_data), 200

        offset = (page - 1) * per_page

        if category:
            query = """
                SELECT creator_id, name, bio, created_at, total_content, followers, verified, category
                FROM content_creators
                WHERE category = %s
                ORDER BY followers DESC
                LIMIT %s OFFSET %s
            """
            params = (category, per_page, offset)
        else:
            query = """
                SELECT creator_id, name, bio, created_at, total_content, followers, verified, category
                FROM content_creators
                ORDER BY followers DESC
                LIMIT %s OFFSET %s
            """
            params = (per_page, offset)

        results = execute_query(query, params, fetch=True)

        creators = []
        if results:
            for row in results:
                creators.append({
                    'id': row[0],
                    'name': row[1],
                    'bio': row[2],
                    'created_at': row[3].isoformat(),
                    'total_content': row[4],
                    'followers': row[5],
                    'verified': row[6],
                    'category': row[7]
                })

        response_data = {
            'total': len(creators),
            'page': page,
            'per_page': per_page,
            'creators': creators
        }

        set_in_cache(cache_key, response_data, ttl=60)

        return jsonify(response_data), 200

@app.route('/api/creators/<creator_id>', methods=['GET'])
def get_creator(creator_id):
    """Get specific creator details"""
    with tracer.start_as_current_span("get_creator") as span:
        creator_requests_counter.add(1, {"endpoint": "/api/creators/:id", "method": "GET"})
        span.set_attribute("creator.id", creator_id)

        cache_key = f"creator:{creator_id}"
        cached_data = get_from_cache(cache_key)

        if cached_data:
            return jsonify(cached_data), 200

        query = """
            SELECT creator_id, name, bio, created_at, total_content, followers, verified, category
            FROM content_creators
            WHERE creator_id = %s
        """

        result = execute_query(query, (creator_id,), fetch=True)

        if not result:
            return jsonify({'error': 'Creator not found'}), 404

        row = result[0]
        creator_data = {
            'id': row[0],
            'name': row[1],
            'bio': row[2],
            'created_at': row[3].isoformat(),
            'total_content': row[4],
            'followers': row[5],
            'verified': row[6],
            'category': row[7]
        }

        set_in_cache(cache_key, creator_data, ttl=300)

        return jsonify(creator_data), 200

@app.route('/api/content', methods=['POST'])
def create_content():
    """Create new content"""
    with tracer.start_as_current_span("create_content") as span:
        start_time = time.time()
        creator_requests_counter.add(1, {"endpoint": "/api/content", "method": "POST"})

        data = request.get_json() or {}
        creator_id = data.get('creator_id')

        if not creator_id:
            return jsonify({'error': 'creator_id is required'}), 400

        # Simulate content processing time
        creation_delay = random.uniform(0.05, 0.3)
        time.sleep(creation_delay)

        content_type = data.get('type', random.choice(CONTENT_TYPES))
        title = data.get('title', f'{content_type.capitalize()} content')
        description = data.get('description', f'Description for {title}')
        duration_seconds = random.randint(30, 600) if content_type in ['video', 'audio'] else None
        file_size_mb = round(random.uniform(1.0, 500.0), 2)

        content_id = f'content_{int(time.time() * 1000000) % 1000000}_{random.randint(100, 999)}'

        query = """
            INSERT INTO content_items (content_id, creator_id, type, title, description, duration_seconds, file_size_mb)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING content_id, type, title, created_at
        """

        result = execute_query(query, (content_id, creator_id, content_type, title, description, duration_seconds, file_size_mb), fetch=True)

        if result:
            # Update creator content count
            execute_query(
                "UPDATE content_creators SET total_content = total_content + 1 WHERE creator_id = %s",
                (creator_id,)
            )

            row = result[0]
            content_data = {
                'id': row[0],
                'creator_id': creator_id,
                'type': row[1],
                'title': row[2],
                'created_at': row[3].isoformat(),
                'views': 0,
                'likes': 0,
                'duration_seconds': duration_seconds,
                'file_size_mb': file_size_mb
            }

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

            # Invalidate caches
            invalidate_cache(f"creator:{creator_id}")
            invalidate_cache("stats:*")
            invalidate_cache("content:*")

            logger.info(f"Content created: {content_id} by {creator_id} (type: {content_type})")

            return jsonify(content_data), 201
        else:
            return jsonify({'error': 'Failed to create content'}), 500

@app.route('/api/content', methods=['GET'])
def get_content():
    """Get all content with pagination and filtering"""
    with tracer.start_as_current_span("get_content"):
        creator_requests_counter.add(1, {"endpoint": "/api/content", "method": "GET"})

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        content_type = request.args.get('type')

        offset = (page - 1) * per_page

        if content_type:
            query = """
                SELECT content_id, creator_id, type, title, created_at, views, likes
                FROM content_items
                WHERE type = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (content_type, per_page, offset)
        else:
            query = """
                SELECT content_id, creator_id, type, title, created_at, views, likes
                FROM content_items
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (per_page, offset)

        results = execute_query(query, params, fetch=True)

        content_list = []
        if results:
            for row in results:
                content_list.append({
                    'id': row[0],
                    'creator_id': row[1],
                    'type': row[2],
                    'title': row[3],
                    'created_at': row[4].isoformat(),
                    'views': row[5],
                    'likes': row[6]
                })

        return jsonify({
            'total': len(content_list),
            'page': page,
            'per_page': per_page,
            'content': content_list
        }), 200

@app.route('/api/content/<content_id>', methods=['GET'])
def get_content_item(content_id):
    """Get specific content item"""
    with tracer.start_as_current_span("get_content_item") as span:
        creator_requests_counter.add(1, {"endpoint": "/api/content/:id", "method": "GET"})
        span.set_attribute("content.id", content_id)

        cache_key = f"content:{content_id}"
        cached_data = get_from_cache(cache_key)

        if cached_data:
            return jsonify(cached_data), 200

        query = """
            SELECT content_id, creator_id, type, title, description, created_at, views, likes, duration_seconds, file_size_mb
            FROM content_items
            WHERE content_id = %s
        """

        result = execute_query(query, (content_id,), fetch=True)

        if not result:
            return jsonify({'error': 'Content not found'}), 404

        row = result[0]
        content_data = {
            'id': row[0],
            'creator_id': row[1],
            'type': row[2],
            'title': row[3],
            'description': row[4],
            'created_at': row[5].isoformat(),
            'views': row[6],
            'likes': row[7],
            'duration_seconds': row[8],
            'file_size_mb': float(row[9]) if row[9] else None
        }

        set_in_cache(cache_key, content_data, ttl=120)

        return jsonify(content_data), 200

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    with tracer.start_as_current_span("get_stats"):
        creator_requests_counter.add(1, {"endpoint": "/api/stats", "method": "GET"})

        cache_key = "stats:overall"
        cached_data = get_from_cache(cache_key)

        if cached_data:
            return jsonify(cached_data), 200

        # Get content by type
        query = """
            SELECT type, COUNT(*), SUM(views), SUM(likes)
            FROM content_items
            GROUP BY type
        """
        results = execute_query(query, fetch=True)

        content_by_type = {}
        if results:
            for row in results:
                content_by_type[row[0]] = {
                    'count': row[1],
                    'views': row[2] or 0,
                    'likes': row[3] or 0
                }

        # Get total stats
        total_query = """
            SELECT
                (SELECT COUNT(*) FROM content_creators) as total_creators,
                (SELECT COUNT(*) FROM content_items) as total_content,
                (SELECT SUM(views) FROM content_items) as total_views,
                (SELECT SUM(likes) FROM content_items) as total_likes
        """
        total_result = execute_query(total_query, fetch=True)

        stats_data = {
            'total_creators': total_result[0][0] if total_result else 0,
            'total_content': total_result[0][1] if total_result else 0,
            'total_views': total_result[0][2] if total_result else 0,
            'total_likes': total_result[0][3] if total_result else 0,
            'content_by_type': content_by_type
        }

        set_in_cache(cache_key, stats_data, ttl=30)

        return jsonify(stats_data), 200

if __name__ == '__main__':
    logger.info("Starting Content Creator Service on port 5001")
    init_db_pool()
    init_redis()
    app.run(host='0.0.0.0', port=5001, debug=False)
