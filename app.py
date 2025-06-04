from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return (
        "✅ Flask App Deployed via Docker and GitHub Actions!!!<br>"
        "🔁 Automatically builds and pushes Docker images on code change.<br>"
        "🚀 Running inside a container served via AWS ALB!"
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

