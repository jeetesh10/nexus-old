#!/bin/bash
set -e
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "\n${CYAN}--- Configuring Vault and External Secrets ---${NC}"

VAULT_POD="vault-0"
VAULT_NAMESPACE="nexus-platform"

# --- Configure Vault ---
echo "  - Enabling and configuring Vault's Kubernetes auth method..."
# Enable the Kubernetes auth method. The '|| true' ignores errors if it's already enabled.
kubectl exec -n ${VAULT_NAMESPACE} ${VAULT_POD} -- vault auth enable kubernetes >/dev/null 2>&1 || true

# Configure the Kubernetes auth method to find the K8s API.
kubectl exec -n ${VAULT_NAMESPACE} ${VAULT_POD} -- vault write auth/kubernetes/config \
    kubernetes_host="https://kubernetes.default.svc" >/dev/null

echo "  - Enabling Vault's KV (Key-Value) secrets engine..."
# Enable the kv-v2 secrets engine. The '|| true' ignores errors if it's already enabled.
kubectl exec -n ${VAULT_NAMESPACE} ${VAULT_POD} -- vault secrets enable -path=secret kv-v2 >/dev/null 2>&1 || true

# --- Create SecretStore for External Secrets Operator ---
echo "  - Creating the Kubernetes SecretStore resource..."
# This SecretStore tells the External Secrets Operator how to connect to our Vault instance.
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: nexus-platform
spec:
  provider:
    vault:
      # The address of the Vault service inside the cluster
      server: "http://vault.nexus-platform.svc:8200"
      # The path where the KV secrets engine is mounted
      path: "secret"
      version: "v2"
      auth:
        # Specifies to use the Kubernetes auth method
        kubernetes:
          mountPath: "kubernetes"
          # A role that will be created later to grant specific permissions
          role: "nexus-platform-role"
          # We will grant permissions to the default service account in the namespace
          serviceAccountRef:
            name: default
EOF

echo -e "\n${GREEN}✅ Vault configuration and SecretStore creation complete.${NC}"