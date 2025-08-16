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

echo -e "\n${CYAN}--- Deploying Linkerd Service Mesh for [${YELLOW}$ENV_TYPE${CYAN}] environment ---${NC}"

# Generate and apply CRDs first
echo "  - Applying Linkerd CRDs..."
linkerd install --crds | kubectl apply -f -

# Wait for CRDs to be registered by the Kubernetes API server
sleep 5

# Generate and apply the control plane
echo "  - Applying Linkerd Control Plane..."
linkerd install | kubectl apply -f - --validate=false
echo "  - Waiting for control plane to be ready..."
linkerd check

# Generate and apply the viz extension
echo "  - Applying Linkerd Viz Extension..."
linkerd viz install | kubectl apply -f - --validate=false
echo "  - Waiting for viz extension to be ready..."
linkerd viz check

echo -e "\n${GREEN}✅ Linkerd deployment complete for [${YELLOW}$ENV_TYPE${GREEN}].${NC}"
