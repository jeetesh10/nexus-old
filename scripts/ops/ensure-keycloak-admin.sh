#!/usr/bin/env bash
set -euo pipefail

# Keep a stable local port-forward for Keycloak Admin on port 18081 by default.
# This follows the convention that 18081 is reserved for Keycloak admin UI.
# Usage:
#   ./scripts/ops/ensure-keycloak-admin.sh           # forwards to localhost:18081
#   KEYCLOAK_LOCAL_PORT=18081 ./scripts/ops/ensure-keycloak-admin.sh
#   NAMESPACE=default ./scripts/ops/ensure-keycloak-admin.sh

NAMESPACE=${NAMESPACE:-default}
PORT=${KEYCLOAK_LOCAL_PORT:-18081}
SVC=${SVC:-keycloak-service}
TARGET_PORT=${TARGET_PORT:-8080}

BLUE="\033[0;34m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"; NC="\033[0m"

echo -e "${BLUE}Ensuring port-forward:${NC} service/${SVC} -> localhost:${PORT} (service port ${TARGET_PORT}, ns=${NAMESPACE})"

if command -v lsof >/dev/null 2>&1 && lsof -iTCP -sTCP:LISTEN -P | grep -q ":${PORT} "; then
  echo -e "${YELLOW}Port ${PORT} is already in use on localhost.${NC}"
  echo -e "Use a different port: ${GREEN}KEYCLOAK_LOCAL_PORT=19081 $0${NC}"
  exit 1
fi

echo -e "${GREEN}Keycloak Admin:${NC} http://localhost:${PORT}/"
echo -e "${YELLOW}Press Ctrl+C to stop. The script will automatically restart the port-forward if it drops.${NC}\n"

while true; do
  kubectl port-forward service/${SVC} ${PORT}:${TARGET_PORT} -n ${NAMESPACE} --address 127.0.0.1 || true
  echo -e "${YELLOW}Port-forward ended. Restarting in 2 seconds...${NC}"
  sleep 2
done
