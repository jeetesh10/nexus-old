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

echo -e "\n${CYAN}--- Setting up Kubernetes Cluster for [${YELLOW}$ENV_TYPE${CYAN}] environment ---${NC}"

# --- Cluster Creation (only for 'kind') ---
if [ "$CLUSTER_PROVIDER" == "kind" ]; then
  echo "  - Provider is 'kind'. Setting up local cluster."
  if [ "$(kind get clusters | grep -x kind)" ]; then
    echo "  - Deleting existing Kind cluster for a clean start..."
    kind delete cluster
  fi
  echo "  - Creating new Kind cluster with required port mappings..."
  kind create cluster --config iac/kubernetes/kind-config.yaml
else
  echo "  - Provider is 'cloud'. Skipping cluster creation."
  echo "  - Verifying connection to existing cluster..."
  kubectl cluster-info > /dev/null
  echo "  - Connection successful. Current context: $(kubectl config current-context)"
fi

# --- Helm Setup (for all environments) ---
echo "  - Configuring Helm repositories..."
# Add repos only if they don't already exist
if ! helm repo list | grep -q '^bitnami\s'; then
  helm repo add bitnami https://charts.bitnami.com/bitnami
fi
# Always update repos to get the latest chart versions
helm repo update

# --- Namespace Creation (for all environments) ---
echo "  - Applying namespace..."
kubectl apply -f iac/kubernetes/base/namespace.yaml

echo -e "\n${GREEN}✅ Cluster setup complete for [${YELLOW}$ENV_TYPE${GREEN}].${NC}"
