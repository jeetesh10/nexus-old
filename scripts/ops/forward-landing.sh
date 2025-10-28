#!/usr/bin/env bash
set -euo pipefail

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}Starting port-forward for Landing/Admin...${NC}"

# Stop any previous matching port-forward
pkill -f "kubectl port-forward .*admin-dashboard-internal 8081:80" 2>/dev/null || true

kubectl port-forward service/admin-dashboard-internal 8081:80 >/dev/null 2>&1 &
PF_PID=$!

sleep 2

if ps -p $PF_PID >/dev/null 2>&1; then
  echo -e "${GREEN}Landing page available:${NC} http://localhost:8081/"
  echo -e "${GREEN}Admin dashboard:${NC} http://localhost:8081/admin"
  echo -e "${YELLOW}(Ctrl+C doesn’t stop the background port-forward; to stop later run:)${NC} pkill -f 'kubectl port-forward .*admin-dashboard-internal 8081:80'"
else
  echo -e "${YELLOW}Port-forward did not start successfully. Check that service/admin-dashboard-internal exists and is Ready.${NC}"
  exit 1
fi
