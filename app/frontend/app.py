from flask import Flask, render_template_string
import requests

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # Call backend service (use Kubernetes service name)
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