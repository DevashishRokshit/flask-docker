#!/bin/bash
cd /home/ec2-user/flask-app
docker stop flask-app || true
docker rm flask-app || true
docker pull devashishrokshit/flask-app:latest
docker run -d -p 80:5000 --name flask-app devashishrokshit/flask-app:latest

