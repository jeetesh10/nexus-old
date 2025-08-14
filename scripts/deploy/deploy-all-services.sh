#!/bin/bash

# This script deploys all components of the Nexus platform.
# It will evolve as more services are added.

set -e # Exit immediately if a command exits with a non-zero status.

echo "🚀 Deploying Nexus Platform..."

# --- Deploy Base Components ---
echo "Applying Namespace..."
kubectl apply -f nexus/iac/kubernetes/base/namespace.yaml

echo "Applying ConfigMap and Network Policies..."
kubectl apply -f nexus/iac/kubernetes/base/configmap.yaml
kubectl apply -f nexus/iac/kubernetes/base/default-deny-ingress.yaml

echo "Applying Service Mesh..."
kubectl apply -f nexus/iac/kubernetes/base/service-mesh.yaml

# --- Deploy Monitoring Stack ---
echo "Applying monitoring components (Grafana, Prometheus, Loki, Alertmanager)..."
kubectl apply -f nexus/iac/kubernetes/monitoring/

echo "✅ Nexus Platform deployment initiated."
echo

# --- Interactive Post-Deployment Steps ---

# Prompt user to check pod status
read -p "Do you want to watch the pod status now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl get pods -n nexus-platform -w
fi

echo

# Prompt user to start port-forwarding for monitoring services
read -p "Do you want to start port-forwarding for monitoring services? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting port-forwarding in the background..."

    # Kill any previous port-forwards to prevent errors
    pkill -f "kubectl port-forward" || true

    # Start new port-forwards as background jobs
    kubectl port-forward svc/grafana-service 3000:3000 -n nexus-platform &
    kubectl port-forward svc/prometheus-service 9090:9090 -n nexus-platform &
    kubectl port-forward svc/alertmanager-service 9093:9093 -n nexus-platform &

    GREEN='\033[0;32m'
    NC='\033[0m' # No Color

    echo -e "${GREEN}Services are now accessible at:${NC}"
    echo "  - Grafana:       http://localhost:3000"
    echo "  - Prometheus:    http://localhost:9090"
    echo "  - Alertmanager:  http://localhost:9093"
    echo
    echo "NOTE: Port-forwarding is running in the background."
    echo "To stop it later, run the command: pkill -f \"kubectl port-forward\""
fi
