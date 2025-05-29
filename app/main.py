# app/main.py
from flask import Flask
from telemetry.tracer import configure_tracer

# Initialize tracing before app starts
configure_tracer("payment-service")

app = Flask(__name__)

@app.route("/pay")
def process_payment():
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process-payment"):
        # Your business logic here
        return "Payment processed"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)