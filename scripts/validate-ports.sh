#!/usr/bin/env bash
# Simple validator: ensure iac/kubernetes manifests reference ports from config/ports.yaml
# Requirements: yq (mikefarah/yq)
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORTS_FILE="$ROOT_DIR/config/ports.yaml"
MANIFEST_DIRS=("iac" "deploy" "k8s" "iac/kubernetes")

if ! command -v yq >/dev/null 2>&1; then
  echo "ERROR: yq is required. Install from https://github.com/mikefarah/yq"
  exit 2
fi

if [ ! -f "$PORTS_FILE" ]; then
  echo "No $PORTS_FILE found — skipping ports validation."
  exit 0
fi

errors=0

services=$(yq e '.services | keys | .[]' "$PORTS_FILE")
for svc in $services; do
  containerPort=$(yq e ".services.$svc.containerPort // \"\" " "$PORTS_FILE")
  servicePort=$(yq e ".services.$svc.servicePort // \"\" " "$PORTS_FILE")

  if [ -n "$containerPort" ]; then
    matches=$(grep -R --line-number --include \*.yaml --include \*.yml -E "containerPort:[[:space:]]*$containerPort|targetPort:[[:space:]]*$containerPort" "${MANIFEST_DIRS[@]}" 2>/dev/null || true)
    if [ -z "$matches" ]; then
      echo "ERROR: service '$svc' containerPort $containerPort not found in manifests under ${MANIFEST_DIRS[*]}."
      errors=$((errors+1))
    fi
  fi

  if [ -n "$servicePort" ]; then
    matches=$(grep -R --line-number --include \*.yaml --include \*.yml -E "port:[[:space:]]*$servicePort|servicePort:[[:space:]]*$servicePort" "${MANIFEST_DIRS[@]}" 2>/dev/null || true)
    if [ -z "$matches" ]; then
      echo "WARN: service '$svc' servicePort $servicePort not found in manifests under ${MANIFEST_DIRS[*]}."
    fi
  fi
done

if [ $errors -gt 0 ]; then
  echo "Ports validation failed. Update manifests or config/ports.yaml."
  exit 1
fi

echo "Ports validation passed."
exit 0
