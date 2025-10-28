#!/usr/bin/env bash
# Canonical manager for local MongoDB stack (start|stop|restart|status|logs|wait)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT/iac/local-db/docker-compose.yml}"
ENV_FILE="${ENV_FILE:-$ROOT/iac/local-db/.env.mongo}"
MONGO_CONTAINER="${MONGO_CONTAINER:-local-mongo}"
MONGO_EXP_CONTAINER="${MONGO_EXP_CONTAINER:-local-mongo-express}"

run_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" "$@"
  else
    docker-compose -f "$COMPOSE_FILE" "$@"
  fi
}

start() {
  echo "Starting Mongo stack using $COMPOSE_FILE"
  run_compose up -d
  echo "Waiting for Mongo to be ready..."
  wait_for_mongo 30
  echo "Mongo stack started."
}

stop() {
  echo "Stopping Mongo stack..."
  run_compose down
  echo "Stopped."
}

status() {
  docker ps --filter "name=${MONGO_CONTAINER}" --filter "name=${MONGO_EXP_CONTAINER}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

logs() {
  run_compose logs -f --tail=200
}

wait_for_mongo() {
  local timeout=${1:-30}
  local deadline=$((SECONDS + timeout))
  while (( SECONDS < deadline )); do
    if docker exec "$MONGO_CONTAINER" mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
      echo "Mongo responded via mongosh."
      return 0
    fi
    if command -v nc >/dev/null 2>&1 && nc -z localhost 27017 >/dev/null 2>&1; then
      echo "Mongo TCP port open on localhost:27017."
      return 0
    fi
    if command -v curl >/dev/null 2>&1 && curl -sS --max-time 2 http://localhost:8081 >/dev/null 2>&1; then
      echo "mongo-express reachable on http://localhost:8081."
      return 0
    fi
    sleep 1
  done
  echo "Timed out waiting for Mongo after ${timeout}s" >&2
  return 1
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  logs) logs ;;
  wait) wait_for_mongo 30 ;;
  *) 
    cat <<EOF
Usage: $0 {start|stop|restart|status|logs|wait}
EOF
    exit 1
    ;;
esac