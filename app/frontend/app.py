from flask import Flask, render_template_string
import requests
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

app = Flask(__name__)

# Initialize OpenTelemetry
metrics.get_meter_provider().shutdown()
meter = metrics.get_meter("frontend-service")
counter = meter.create_counter("http.requests", description="Total HTTP requests")

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("frontend-service")
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger.monitoring.svc.cluster.local:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
metrics.set_meter_provider(MeterProvider(metric_readers=[PrometheusMetricReader()]))

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

@app.route('/')
def index():
    counter.add(1)
    with tracer.start_as_current_span("frontend-request"):
        try:
            response = requests.get('http://backend-service:5000/api')
            message = response.json().get('message', 'Error: Backend unavailable')
        except:
            message = 'Error: Backend unavailable'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Microservice Monitoring Demo</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            h1 {{ color: #2c3e50; }}
            p {{ font-size: 18px; color: #34495e; }}
        </style>
    </head>
    <body>
        <h1>Microservice Monitoring Demo</h1>
        <p>Backend says: {message}</p>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)