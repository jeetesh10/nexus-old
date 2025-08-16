#!/bin/bash
set -e
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${CYAN}--- Creating Vault Policy and Role for Nexus Platform ---${NC}"

VAULT_POD="vault-0"
VAULT_NAMESPACE="nexus-platform"

# --- Create Vault Policy ---
echo "  - Creating Vault policy: nexus-platform-policy"
# This policy grants read-only access to secrets stored under 'secret/data/nexus-platform/'.
# The 'data/' part is required for the kv-v2 secrets engine.
cat <<EOF | kubectl exec -i -n ${VAULT_NAMESPACE} ${VAULT_POD} -- vault policy write nexus-platform-policy -
path "secret/data/nexus-platform/*" {
  capabilities = ["read"]
}
EOF

# --- Create Vault Role ---
echo "  - Creating Vault role: nexus-platform-role"
# This role binds the policy to the 'default' service account in the 'nexus-platform' namespace.
# Any pod using this service account in this namespace can now assume this role.
kubectl exec -n ${VAULT_NAMESPACE} ${VAULT_POD} -- vault write auth/kubernetes/role/nexus-platform-role \
    bound_service_account_names=default \
    bound_service_account_namespaces=${VAULT_NAMESPACE} \
    policies=nexus-platform-policy \
    ttl=24h >/dev/null

echo -e "\n${GREEN}✅ Vault policy and role created successfully.${NC}"