#!/usr/bin/env bash
# filepath: /workspaces/nexus/services/mybot/scripts/start-mybot.sh
#
# Start the mybot service (Codespaces / dev-container friendly)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# Config
PORT="${PORT:-4000}"
HOST="${HOST:-0.0.0.0}"        # ensure accessible in Codespaces
HEALTH_PATH="${HEALTH_PATH:-/api/health}"
START_TIMEOUT="${START_TIMEOUT:-45}"
LOG_DIR="${LOG_DIR:-${ROOT_DIR}/logs}"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/mybot.log}"
DAEMON="false"

# Usage function
usage() {
  echo "Usage: $0 [--daemon] [--timeout <sec>]"
  exit 1
}

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --daemon) DAEMON="true"; shift ;;
    --timeout) START_TIMEOUT="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1"; usage ;;
  esac
done

mkdir -p "$LOG_DIR"

# Check node/npm
if ! command -v node >/dev/null 2>&1; then
  echo "Node.js not found" >&2
  exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found" >&2
  exit 1
fi

# Load environment
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

export PORT HOST

# Install dependencies
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

# Choose start command
PKG_SCRIPTS="$(node -e "try{console.log(JSON.stringify(require('./package.json').scripts||{}))}catch(e){console.log('{}')}")"
if echo "$PKG_SCRIPTS" | grep -q '"dev"'; then
  START_CMD="npm run dev"
elif echo "$PKG_SCRIPTS" | grep -q '"start"'; then
  START_CMD="npm start"
else
  # fallback heuristics
  if [[ -f server.js ]]; then
    START_CMD="node server.js"
  else
    echo "No start or dev script and no server.js found." >&2
    exit 1
  fi
fi

# ---- new: ensure nodemon is available when start uses dev script ----
if echo "$START_CMD" | grep -q "nodemon"; then
  if command -v nodemon >/dev/null 2>&1 || [[ -x "./node_modules/.bin/nodemon" ]]; then
    echo "nodemon found -> ok"
  else
    echo "nodemon not found, falling back to node src/index.js"
    if [[ -f src/index.js ]]; then
      START_CMD="node src/index.js"
    else
      echo "nodemon missing and src/index.js not found. Install nodemon or add a start script." >&2
      exit 1
    fi
  fi
fi

echo "Starting mybot with: $START_CMD (PORT=$PORT HOST=$HOST)"
echo "Logs: $LOG_FILE"

# Start service
if [[ "$DAEMON" == "true" ]]; then
  nohup bash -c "$START_CMD" >>"$LOG_FILE" 2>&1 &
  PID=$!
  echo "Started in background (pid $PID)"
else
  # Start in background but keep tail following for interactive convenience
  bash -c "$START_CMD" >>"$LOG_FILE" 2>&1 &
  PID=$!
  echo "Started (pid $PID)"
fi

# Health check loop
echo "Waiting up to ${START_TIMEOUT}s for health at http://127.0.0.1:${PORT}${HEALTH_PATH}"
end=$((SECONDS + START_TIMEOUT))
healthy="false"
while [[ $SECONDS -lt $end ]]; do
  if curl -fsS "http://127.0.0.1:${PORT}${HEALTH_PATH}" >/dev/null 2>&1; then
    healthy="true"
    break
  fi
  # If no explicit health endpoint yet, try root once near end
  if [[ $((end-SECONDS)) -le 5 ]]; then
    if curl -fsS "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
      healthy="true"
      break
    fi
  fi
  sleep 1
done

if [[ "$healthy" != "true" ]]; then
  echo "Service not healthy within timeout."
  echo "Last 60 log lines:"
  tail -n 60 "$LOG_FILE" || true
  exit 2
fi

echo "Service is healthy."

# Codespaces helper
if [[ -n "${CODESPACE_NAME:-}" ]]; then
  CODESPACE_URL="https://${CODESPACE_NAME}-${PORT}.app.github.dev"
  echo "Codespaces URL: $CODESPACE_URL"
  if [[ -n "${BROWSER:-}" ]]; then
    "$BROWSER" "$CODESPACE_URL" || true
  fi
else
  if [[ -n "${BROWSER:-}" ]]; then
    "$BROWSER" "http://127.0.0.1:${PORT}/" || true
  fi
fi

if [[ "$DAEMON" == "true" ]]; then
  echo "Running in daemon mode. Tail logs with:"
  echo "  tail -f $LOG_FILE"
else
  echo "Tailing logs (Ctrl-C to stop tail; service keeps running)."
  tail -n 50 -f "$LOG_FILE"
fi