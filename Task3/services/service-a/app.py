from flask import Flask
import requests
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Настраиваем tracer provider
trace.set_tracer_provider(
   TracerProvider(
       resource=Resource.create({SERVICE_NAME: "service-a"})
   )
)

# Создаем Jaeger экспортер
jaeger_exporter = JaegerExporter(
   agent_host_name="jaeger",
   agent_port=6831,
)

# Добавляем обработчик
trace.get_tracer_provider().add_span_processor(
   BatchSpanProcessor(jaeger_exporter)
)

# Создаем tracer - ЭТО ВАЖНАЯ СТРОКА!
tracer = trace.get_tracer(__name__)

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


@app.route("/")
def root():
    # simple span and call to service-b
    with tracer.start_as_current_span("service-a:root"):
        try:
            r = requests.get("http://service-b:8080/")
            return f"service-a -> service-b: {r.text}\n"
        except Exception as e:
            return f"service-a error: {e}\n", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)