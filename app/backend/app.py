from flask import Flask, jsonify
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
counter = meter.create_counter("http.requests", description="Total HTTP requests")

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("backend-service")
otlp_exporter = OTLPSpanExporter(endpoint="http://jaeger.monitoring.svc.cluster.local:4318/v1/traces")
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
metrics.set_meter_provider(MeterProvider(metric_readers=[PrometheusMetricReader()]))

FlaskInstrumentor().instrument_app(app)

@app.route('/api', methods=['GET'])
def get_message():
    counter.add(1)
    with tracer.start_as_current_span("backend-api"):
        return jsonify({"message": "Hello from backend!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)