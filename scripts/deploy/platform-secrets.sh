#!/bin/bash
set -e
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Cleanup function
cleanup() {
    echo -e "\n${CYAN}--- Cleaning up Secrets Management ---${NC}"
    helm uninstall vault -n nexus-platform || true
    helm uninstall external-secrets -n external-secrets || true
    kubectl delete namespace nexus-platform || true
    kubectl delete namespace external-secrets || true
    echo -e "\n${GREEN}✅ Secrets Management cleanup complete.${NC}"
}

deploy() {
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
echo "  - Deploying HashiCorp Vault..."
helm repo add hashicorp https://helm.releases.hashicorp.com >/dev/null 2>&1 || true
helm repo update >/dev/null

# Production-ready configuration for Vault
# Disables dev mode, enables HA with Raft integrated storage and persistent volumes.
helm upgrade --install vault hashicorp/vault \
  --namespace nexus-platform --create-namespace \
  --set "server.ha.enabled=true" \
  --set "server.ha.raft.enabled=true" \
  --set "server.ha.replicas=1" \
  --set "server.ha.storage.raft.enabled=true" \
  --set "server.dataStorage.size=10Gi" \
  --set "server.auditStorage.size=10Gi"

echo "  - Waiting for Vault StatefulSet to start..."
# Add a small delay to allow the StatefulSet controller to create the pod
sleep 5
# The pod will be 'Running' but not 'Ready' until unsealed.
# We wait for the pod to be initialized, which means the container has started.
kubectl wait --for=condition=Initialized pod \
  --selector="app.kubernetes.io/name=vault" \
  --namespace=nexus-platform --timeout=3m

# Check if Vault is initialized by checking the 'Initialized' status from vault status command
# The command fails if the vault is not initialized
if ! kubectl exec vault-0 -n nexus-platform -- vault status >/dev/null 2>&1; then
    echo "  - Vault not initialized. Initializing and unsealing..."
    # Initialize Vault and capture the keys. Storing in a temporary file.
    kubectl exec vault-0 -n nexus-platform -- vault operator init -key-shares=1 -key-threshold=1 -format=json > /tmp/vault-keys.json
    
    VAULT_UNSEAL_KEY=$(cat /tmp/vault-keys.json | jq -r ".unseal_keys_b64[0]")
    VAULT_ROOT_TOKEN=$(cat /tmp/vault-keys.json | jq -r ".root_token")

    # Unseal Vault
    kubectl exec vault-0 -n nexus-platform -- vault operator unseal $VAULT_UNSEAL_KEY

    # Store the root token in a Kubernetes secret for other services to use
    kubectl create secret generic vault-credentials \
        -n nexus-platform \
        --from-literal=root-token=$VAULT_ROOT_TOKEN \
        --from-literal=unseal-key=$VAULT_UNSEAL_KEY || true # || true to prevent error if it already exists
    
    rm /tmp/vault-keys.json
    echo "  - Vault initialized and unsealed. Root token and unseal key stored in 'vault-credentials' secret."
else
    echo "  - Vault already initialized and unsealed."
fi

echo "  - Waiting for Vault pod to be fully Ready..."
# Now wait for the pod to be fully Ready (which it should be after unsealing)
kubectl wait --for=condition=Ready pod \
  --selector="app.kubernetes.io/name=vault" \
  --namespace=nexus-platform --timeout=5m

echo -e "\n${GREEN}✅ Secrets Management deployment complete for [${YELLOW}$ENV_TYPE${GREEN}].${NC}"
}

# Main execution logic
if [[ "$1" == "--cleanup" ]]; then
    cleanup
else
    # This script expects the config file path to be passed as the first argument
    if [ -z "$1" ]; then
      echo "Usage: $0 /path/to/environment.env or --cleanup"
      exit 1
    fi
    source $1
    deploy
fi