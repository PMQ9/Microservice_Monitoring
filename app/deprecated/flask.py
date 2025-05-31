from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Initialize tracing
provider = TracerProvider()
jaeger_exporter = JaegerExporter(
    agent_host_name="simplest-jaeger-agent.observability",
    agent_port=6831
)
provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
trace.set_tracer_provider(provider)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)