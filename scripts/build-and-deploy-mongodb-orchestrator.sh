#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="nexus/mongodb-orchestrator:latest"
SERVICE_DIR="services/mongodb-orchestrator"

echo "Building ${IMAGE_NAME}..."
docker build -t ${IMAGE_NAME} ${SERVICE_DIR}

if command -v kind >/dev/null 2>&1; then
  echo "Loading image into kind cluster..."
  kind load docker-image ${IMAGE_NAME} || true
fi

echo "Applying Kubernetes manifests..."
kubectl apply -f iac/kubernetes/mongodb-orchestrator-deployment.yaml

echo "Waiting for rollout..."
kubectl rollout status deployment/mongodb-orchestrator -n default --timeout=300s

echo "Done."
