from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return """
    ✅ Flask App Deployed via Docker and GitHub Actions!!!
    🚀 Auto Deployment with CodeDeploy & ASG Successful.
    📦 Image pulled from Docker Hub.
    """

@app.route('/health')
def health_check():
    return jsonify(status="UP", message="App is running correctly"), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

