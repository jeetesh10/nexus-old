#!/bin/bash
set -e


# 1. Build and load all images
./scripts/build-and-load-all.sh

# 2. Install APISIX Ingress Controller (Helm)
echo "\n[INFO] Installing APISIX Ingress Controller..."
kubectl create namespace apisix --context kind-nexus || true
helm repo add apisix https://charts.apiseven.com
helm repo update
helm upgrade --install apisix-ingress apisix/apisix-ingress-controller \
	--namespace apisix --set ingressController.enabled=true --set gateway.type=NodePort --kube-context kind-nexus


# 3. Install Linkerd (CLI)
echo "\n[INFO] Installing Linkerd..."
kubectl create namespace linkerd --context kind-nexus || true
curl -sL https://run.linkerd.io/install | sh
export PATH=$PATH:$HOME/.linkerd2/bin
# Install Linkerd CRDs first
linkerd install --crds --context kind-nexus | kubectl apply --context kind-nexus -f -
# Install or upgrade Linkerd control plane
if kubectl get configmap -n linkerd linkerd-config --context kind-nexus >/dev/null 2>&1; then
	echo "[INFO] Linkerd already installed, running upgrade..."
	linkerd upgrade --context kind-nexus | kubectl apply --context kind-nexus -f -
else
	echo "[INFO] Installing Linkerd control plane..."
	linkerd install --context kind-nexus | kubectl apply --context kind-nexus -f -
fi
linkerd check --context kind-nexus || true

# 4. Install kube-prometheus-stack (Prometheus, Grafana, Alertmanager)
echo "\n[INFO] Installing kube-prometheus-stack..."
kubectl create namespace monitoring --context kind-nexus || true
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
	--namespace monitoring --set grafana.enabled=true --set alertmanager.enabled=true --set prometheus.enabled=true --kube-context kind-nexus

# 5. Apply all custom manifests
kubectl apply -f iac/kubernetes/ --context kind-nexus
kubectl apply -f services/admin-dashboard-service/kubernetes/ --context kind-nexus
kubectl apply -f services/auth/keycloak-service/kubernetes/ --context kind-nexus

# 6. Wait for all pods to be ready (timeout 300s)
echo "\nWaiting for all pods to be ready..."
kubectl wait --for=condition=Ready pods --all --all-namespaces --timeout=300s --context kind-nexus

# 7. Print summary
echo "\nService status summary:"
kubectl get pods,svc,ingress --all-namespaces --context kind-nexus

echo "\nPlatform is deployed to kind cluster 'nexus'."
