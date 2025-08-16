#!/bin/bash
set -e
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# This script expects the config file path to be passed as the first argument
if [ -z "$1" ]; then
  echo "Usage: $0 /path/to/environment.env"
  exit 1
fi
source $1

echo -e "\n${CYAN}--- Deploying Secrets Management for [${YELLOW}$ENV_TYPE${CYAN}] environment ---${NC}"

# --- External Secrets Operator ---
echo "  - Deploying External Secrets Operator..."
helm repo add external-secrets https://charts.external-secrets.io >/dev/null 2>&1 || true
helm repo update >/dev/null
helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace \
  --set installCRDs=true

echo "  - Waiting for External Secrets Operator to be ready..."
kubectl rollout status deployment/external-secrets -n external-secrets --timeout=5m

# --- HashiCorp Vault ---
echo "  - Deploying HashiCorp Vault in dev mode..."
helm repo add hashicorp https://helm.releases.hashicorp.com >/dev/null 2>&1 || true
helm repo update >/dev/null
helm upgrade --install vault hashicorp/vault \
  --namespace nexus-platform \
  --set "server.dev.enabled=true"

echo "  - Waiting for Vault to be ready..."
# Use 'kubectl wait' which is more reliable for StatefulSets than 'rollout status'.
kubectl wait --for=condition=Ready pod \
  --selector="app.kubernetes.io/name=vault" \
  --namespace=nexus-platform --timeout=5m

echo -e "\n${GREEN}✅ Secrets Management deployment complete for [${YELLOW}$ENV_TYPE${GREEN}].${NC}"