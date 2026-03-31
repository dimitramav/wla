#!/usr/bin/env bash
# start.sh — Start all WLA services and wait until healthy.
# Usage: ./scripts/start.sh [--no-frontend]
#
# Services started:
#   MongoDB  (via systemctl)
#   Express  (port 3001)  — logs → /tmp/wla-express.log
#   FastAPI  (port 8000)  — logs → /tmp/wla-fastapi.log
#   Vite     (port 5173)  — logs → /tmp/wla-vite.log   (skip with --no-frontend)
#
# PID file: /tmp/wla.pids  (used by stop.sh)

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NO_FRONTEND=false
[[ "$1" == "--no-frontend" ]] && NO_FRONTEND=true

PIDS_FILE="/tmp/wla.pids"
> "$PIDS_FILE"

# ── helpers ────────────────────────────────────────────────────────────────────

log()  { echo "[wla] $*"; }
die()  { echo "[wla] ERROR: $*" >&2; exit 1; }

wait_for() {
  local name="$1" url="$2" timeout="${3:-60}"
  log "Waiting for $name ($url)..."
  local elapsed=0
  until curl -sf --max-time 2 "$url" >/dev/null 2>&1; do
    sleep 2; elapsed=$((elapsed+2))
    [[ $elapsed -ge $timeout ]] && die "$name did not become healthy after ${timeout}s"
  done
  log "$name is UP"
}

record_pid() {
  echo "$1 $2" >> "$PIDS_FILE"
}

# ── 1. MongoDB ─────────────────────────────────────────────────────────────────

log "Starting MongoDB..."
sudo systemctl start mongod 2>/dev/null || true
sleep 1
mongosh --eval "db.runCommand({ping:1})" --quiet >/dev/null 2>&1 \
  || die "MongoDB failed to start"
log "MongoDB is UP"

# ── 2. Express API (port 3001) ─────────────────────────────────────────────────

log "Starting Express API..."
# Source nvm so node/npm are available
export NVM_DIR="$HOME/.nvm"
# shellcheck source=/dev/null
[[ -s "$NVM_DIR/nvm.sh" ]] && . "$NVM_DIR/nvm.sh"

# Ensure web/.env exists
[[ -f "$ROOT/web/.env" ]] || echo "VITE_API_BASE=http://localhost:3001" > "$ROOT/web/.env"

cd "$ROOT/api"
npm run dev > /tmp/wla-express.log 2>&1 &
EXPRESS_PID=$!
record_pid express $EXPRESS_PID
cd "$ROOT"

wait_for "Express" "http://localhost:3001/health" 30

# ── 3. FastAPI RAG service (port 8000) ─────────────────────────────────────────

log "Starting FastAPI..."
VENV_PYTHON="$ROOT/services/.venv/bin/python"
[[ -x "$VENV_PYTHON" ]] || die ".venv not found — run: python3 -m venv services/.venv && pip install -r services/requirements.txt"

cd "$ROOT/services"
"$VENV_PYTHON" -m uvicorn api.main:app \
  --factory \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info \
  > /tmp/wla-fastapi.log 2>&1 &
FASTAPI_PID=$!
record_pid fastapi $FASTAPI_PID
cd "$ROOT"

wait_for "FastAPI" "http://localhost:8000/health" 60

# ── 4. Vite frontend (port 5173) ───────────────────────────────────────────────

if [[ "$NO_FRONTEND" == false ]]; then
  log "Starting Vite..."
  cd "$ROOT/web"
  npm run dev > /tmp/wla-vite.log 2>&1 &
  VITE_PID=$!
  record_pid vite $VITE_PID
  cd "$ROOT"

  wait_for "Vite" "http://localhost:5173" 30
fi

# ── done ───────────────────────────────────────────────────────────────────────

log ""
log "All services are UP:"
log "  Express  → http://localhost:3001"
log "  FastAPI  → http://localhost:8000"
[[ "$NO_FRONTEND" == false ]] && log "  Vite     → http://localhost:5173"
log ""
log "Logs: /tmp/wla-express.log  /tmp/wla-fastapi.log  /tmp/wla-vite.log"
log "Stop: ./scripts/stop.sh"
