#!/usr/bin/env bash
set -euo pipefail

# Keep a stable local port-forward to the Landing Page service on port 8082 by default (per config/ports.yaml).
# Usage:
#   ./scripts/ops/ensure-landing.sh              # forwards to localhost:18081
#   LANDING_LOCAL_PORT=18081 ./scripts/ops/ensure-landing.sh
#   NAMESPACE=default ./scripts/ops/ensure-landing.sh

NAMESPACE=${NAMESPACE:-default}
PORT=${LANDING_LOCAL_PORT:-8082}
SVC=${SVC:-landing-page}

BLUE="\033[0;34m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"; NC="\033[0m"

echo -e "${BLUE}Ensuring port-forward:${NC} service/${SVC} -> localhost:${PORT} (service port 80, ns=${NAMESPACE})"

if command -v lsof >/dev/null 2>&1 && lsof -iTCP -sTCP:LISTEN -P | grep -q ":${PORT} "; then
  echo -e "${YELLOW}Port ${PORT} is already in use on localhost.${NC}"
  echo -e "Use a different port: ${GREEN}LANDING_LOCAL_PORT=18082 $0${NC}"
  exit 1
fi

echo -e "${GREEN}Landing page:${NC}   http://localhost:${PORT}/"
echo -e "${YELLOW}Press Ctrl+C to stop. The script will automatically restart the port-forward if it drops.${NC}\n"

while true; do
  kubectl port-forward service/${SVC} ${PORT}:80 -n ${NAMESPACE} --address 127.0.0.1 || true
  echo -e "${YELLOW}Port-forward ended. Restarting in 2 seconds...${NC}"
  sleep 2
done
