#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting mock Mongo Orchestrator on port 8001..."
uvicorn dev.mock_orchestrator:app --port 8001 --host 127.0.0.1 &
ORCH_PID=$!

echo "Starting bot-service on port 8085..."
uvicorn src.app.main:app --reload --port 8085 --host 127.0.0.1 &
BOT_PID=$!

echo "Mock orchestrator PID=$ORCH_PID, bot-service PID=$BOT_PID"
echo "To stop: kill $ORCH_PID $BOT_PID"

wait
