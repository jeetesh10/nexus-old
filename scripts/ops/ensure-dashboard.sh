#!/usr/bin/env bash
set -euo pipefail

# Keep a stable local port-forward to the Admin Dashboard service.
# Usage:
#   ./scripts/ops/ensure-dashboard.sh           # forwards to localhost:8081
#   DASHBOARD_LOCAL_PORT=18081 ./scripts/ops/ensure-dashboard.sh
#   NAMESPACE=platform ./scripts/ops/ensure-dashboard.sh

NAMESPACE=${NAMESPACE:-default}
PORT=${DASHBOARD_LOCAL_PORT:-8081}
SVC=${SVC:-admin-dashboard-internal}

BLUE="\033[0;34m"; GREEN="\033[0;32m"; YELLOW="\033[1;33m"; NC="\033[0m"

echo -e "${BLUE}Ensuring port-forward:${NC} service/${SVC} -> localhost:${PORT} (service port 80, ns=${NAMESPACE})"

# If the chosen port is already taken, bail with a helpful tip instead of silently falling back.
if command -v lsof >/dev/null 2>&1 && lsof -iTCP -sTCP:LISTEN -P | grep -q ":${PORT} "; then
  echo -e "${YELLOW}Port ${PORT} is already in use on localhost.${NC}"
  echo -e "Use a different port: ${GREEN}DASHBOARD_LOCAL_PORT=18081 $0${NC}"
  exit 1
fi

echo -e "${GREEN}Landing page:${NC}   http://localhost:${PORT}/"
echo -e "${GREEN}Admin dashboard:${NC} http://localhost:${PORT}/admin"
echo -e "${YELLOW}Press Ctrl+C to stop. The script will automatically restart the port-forward if it drops.${NC}\n"

while true; do
  # Run port-forward in the foreground so Ctrl+C works as expected.
  kubectl port-forward service/${SVC} ${PORT}:80 -n ${NAMESPACE} --address 127.0.0.1 || true
  echo -e "${YELLOW}Port-forward ended. Restarting in 2 seconds...${NC}"
  sleep 2
done
