from flask import Flask
import requests
import os

from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
except Exception:
    OTLPSpanExporter = None

app = Flask(__name__)

# Tracing setup
provider = TracerProvider()
trace.set_tracer_provider(provider)

# Используйте OTLP экспортер вместо Jaeger Thrift
otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger-collector.observability:4317")
if OTLPSpanExporter is not None:
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

tracer = trace.get_tracer(__name__)

@app.route("/")
def root():
    with tracer.start_as_current_span("service-b:root"):
        return "Hello from service-b\n"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)