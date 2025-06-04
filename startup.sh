#!/bin/bash
set -e

# Stop any process using port 80 (typically nginx/httpd)
fuser -k 80/tcp || true

# Navigate to app directory (if needed)
cd /home/ec2-user/flask-app || true

# Stop and remove existing container (if any)
docker stop flask-app || true
docker rm flask-app || true

# Pull latest image
docker pull devashishrokshit/flask-app:latest

# Run the container
docker run -d -p 80:5000 --name flask-app devashishrokshit/flask-app:latest

