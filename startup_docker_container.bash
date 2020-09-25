#!/bin/bash

# Build latest docker image
docker build -t error_classification_server . -f Dockerfile

# Stop docker containers
docker stop ec_server
docker rm ec_server

# Run latest docker image
# Start ECS API
docker run -it --env-file runtime.env \
--name=ec_server \
-p 8000:8000 \
--volume="${HOME}/error_classification_server/ecs.db:/root/.cognicept/ecs.db" \
error_classification_server /src/ecs_endpoint.py