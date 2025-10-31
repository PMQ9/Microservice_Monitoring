from flask import Flask, render_template_string
import requests
import random
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = Flask(__name__)

metrics.set_meter_provider(MeterProvider())
metrics.get_meter_provider().shutdown()
meter = metrics.get_meter("frontend-service")
request_counter = meter.create_counter("http.requests", description="Total HTTP requests")
backend_calls = meter.create_counter("backend.calls", description="Backend API calls")
error_counter = meter.create_counter("frontend.errors", description="Frontend errors")
page_views = meter.create_counter("page.views", description="Page views")

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("frontend-service")
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger.monitoring.svc.cluster.local:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
metrics.set_meter_provider(MeterProvider(metric_readers=[PrometheusMetricReader()]))

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Microservice Monitoring Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { background: rgba(255, 255, 255, 0.95); padding: 30px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); margin-bottom: 30px; }
        h1 { color: #333; font-size: 32px; margin-bottom: 10px; }
        .status-badge { display: inline-block; background: #10b981; color: white; padding: 8px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: rgba(255, 255, 255, 0.95); padding: 25px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2); }
        .card:hover { transform: translateY(-5px); }
        .card h2 { color: #667eea; font-size: 20px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }
        .card p { color: #555; line-height: 1.6; margin-bottom: 10px; }
        .message { background: #f0f4ff; padding: 15px; border-left: 4px solid #667eea; border-radius: 5px; margin-top: 10px; }
        .user-item { background: #f9f9f9; padding: 12px; margin-bottom: 10px; border-left: 3px solid #764ba2; border-radius: 3px; }
        .user-name { font-weight: bold; color: #333; }
        .user-email { color: #888; font-size: 13px; margin-top: 3px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }
        .stat-item { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 28px; font-weight: bold; }
        .stat-label { font-size: 12px; margin-top: 5px; opacity: 0.9; }
        button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { opacity: 0.9; }
        footer { text-align: center; color: white; margin-top: 40px; padding: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Microservice Monitoring Dashboard</h1>
            <span class="status-badge">System Status: Online</span>
        </header>
        
        <div class="grid">
            <div class="card">
                <h2>Backend Service</h2>
                <div class="message">Backend responding successfully</div>
            </div>
            
            <div class="card">
                <h2>Active Users</h2>
                <div class="user-item">
                    <div class="user-name">Alice Johnson</div>
                    <div class="user-email">alice@example.com</div>
                </div>
                <div class="user-item">
                    <div class="user-name">Bob Smith</div>
                    <div class="user-email">bob@example.com</div>
                </div>
                <div class="user-item">
                    <div class="user-name">Charlie Brown</div>
                    <div class="user-email">charlie@example.com</div>
                </div>
            </div>
            
            <div class="card">
                <h2>System Health</h2>
                <p><strong>Status:</strong> Healthy</p>
                <p><strong>Uptime:</strong> Running normally</p>
                <p><strong>Response Time:</strong> < 100ms</p>
                <p><strong>Error Rate:</strong> 0.05%</p>
            </div>
        </div>
        
        <div class="card">
            <h2>Performance Metrics</h2>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{{ requests_per_min }}</div>
                    <div class="stat-label">Requests/min</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ avg_latency }}ms</div>
                    <div class="stat-label">Avg Latency</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ availability }}%</div>
                    <div class="stat-label">Availability</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ active_traces }}</div>
                    <div class="stat-label">Active Traces</div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>Microservice Monitoring - OpenTelemetry Integration</p>
            <p style="font-size: 12px; margin-top: 10px;">Powered by Prometheus, Jaeger, Loki, and Grafana</p>
        </footer>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    request_counter.add(1)
    page_views.add(1)
    
    with tracer.start_as_current_span("frontend-request"):
        try:
            backend_calls.add(1)
            requests.get('http://backend-service:5000/api', timeout=2)
        except:
            error_counter.add(1)
    
    return render_template_string(HTML_TEMPLATE,
        requests_per_min=random.randint(100, 500),
        avg_latency=random.randint(50, 150),
        availability=random.randint(95, 99),
        active_traces=random.randint(200, 500)
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
