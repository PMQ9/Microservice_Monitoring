from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource

def configure_tracer(service_name: str):
    # Set service name that appears in Jaeger
    resource = Resource.create({"service.name": service_name})
    
    # Configure Jaeger exporter
    provider = TracerProvider(resource=resource)
    jaeger_exporter = JaegerExporter(
        agent_host_name="simplest-jaeger-agent.observability",
        agent_port=6831,
    )
    
    # Add processor and set global tracer
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(provider)