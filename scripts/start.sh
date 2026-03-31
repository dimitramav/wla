#!/usr/bin/env bash
# start.sh — Start WLA services and wait until healthy.
#
# Usage: ./scripts/start.sh [PRESET]
#
# Presets (pick one):
#   (none)            Everything: MongoDB + Express + FastAPI + Vite
#   --no-frontend     MongoDB + Express + FastAPI          (backwards-compat alias for --back-fastapi)
#   --backend-only    MongoDB + Express only
#   --fastapi-only    FastAPI only                         (no MongoDB, no Express)
#   --frontend-only   Vite only
#   --front-back      MongoDB + Express + Vite             (no FastAPI)
#   --back-fastapi    MongoDB + Express + FastAPI          (no Vite)
#
# PID file: /tmp/wla.pids  (used by stop.sh)
# Logs:
#   Express  → /tmp/wla-express.log
#   FastAPI  → /tmp/wla-fastapi.log
#   Vite     → /tmp/wla-vite.log

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDS_FILE="/tmp/wla.pids"
> "$PIDS_FILE"

# ── service flags (all on by default) ──────────────────────────────────────────
START_MONGO=true
START_EXPRESS=true
START_FASTAPI=true
START_VITE=true

case "${1:-}" in
  --backend-only)
    START_FASTAPI=false
    START_VITE=false
    ;;
  --fastapi-only)
    START_MONGO=false
    START_EXPRESS=false
    START_VITE=false
    ;;
  --frontend-only)
    START_MONGO=false
    START_EXPRESS=false
    START_FASTAPI=false
    ;;
  --front-back)
    START_FASTAPI=false
    ;;
  --back-fastapi|--no-frontend)
    START_VITE=false
    ;;
  "")
    # default: all services
    ;;
  *)
    echo "Unknown option: $1" >&2
    echo "Valid presets: --backend-only | --fastapi-only | --frontend-only | --front-back | --back-fastapi | --no-frontend" >&2
    exit 1
    ;;
esac

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

if [[ "$START_MONGO" == true ]]; then
  log "Starting MongoDB..."
  sudo systemctl start mongod 2>/dev/null || true
  sleep 1
  mongosh --eval "db.runCommand({ping:1})" --quiet >/dev/null 2>&1 \
    || die "MongoDB failed to start"
  log "MongoDB is UP"
fi

# ── 2. Express API (port 3001) ─────────────────────────────────────────────────

if [[ "$START_EXPRESS" == true ]]; then
  log "Starting Express API..."
  export NVM_DIR="$HOME/.nvm"
  # shellcheck source=/dev/null
  [[ -s "$NVM_DIR/nvm.sh" ]] && . "$NVM_DIR/nvm.sh"

  [[ -f "$ROOT/.env" ]] || echo "VITE_API_BASE=http://localhost:3001" > "$ROOT/.env"

  cd "$ROOT/api"
  npm run dev > /tmp/wla-express.log 2>&1 &
  EXPRESS_PID=$!
  record_pid express $EXPRESS_PID
  cd "$ROOT"

  wait_for "Express" "http://localhost:3001/health" 30
fi

# ── 3. FastAPI RAG service (port 8000) ─────────────────────────────────────────

if [[ "$START_FASTAPI" == true ]]; then
  log "Starting FastAPI..."
  VENV_PYTHON="$ROOT/services/.venv/bin/python"
  [[ -x "$VENV_PYTHON" ]] || die ".venv not found — run: python3 -m venv services/.venv && pip install -r services/requirements.txt"

  cd "$ROOT/services"
  "$VENV_PYTHON" -m uvicorn api.main:create_app \
    --factory \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    > /tmp/wla-fastapi.log 2>&1 &
  FASTAPI_PID=$!
  record_pid fastapi $FASTAPI_PID
  cd "$ROOT"

  wait_for "FastAPI" "http://localhost:8000/health" 60
fi

# ── 4. Vite frontend (port 5173) ───────────────────────────────────────────────

if [[ "$START_VITE" == true ]]; then
  log "Starting Vite..."
  export NVM_DIR="$HOME/.nvm"
  # shellcheck source=/dev/null
  [[ -s "$NVM_DIR/nvm.sh" ]] && . "$NVM_DIR/nvm.sh"

  cd "$ROOT/web"
  npm run dev > /tmp/wla-vite.log 2>&1 &
  VITE_PID=$!
  record_pid vite $VITE_PID
  cd "$ROOT"

  wait_for "Vite" "http://localhost:5173" 30
fi

# ── done ───────────────────────────────────────────────────────────────────────

log ""
log "Services UP:"
[[ "$START_MONGO"   == true ]] && log "  MongoDB  → localhost:27017"
[[ "$START_EXPRESS" == true ]] && log "  Express  → http://localhost:3001"
[[ "$START_FASTAPI" == true ]] && log "  FastAPI  → http://localhost:8000"
[[ "$START_VITE"    == true ]] && log "  Vite     → http://localhost:5173"
log ""
log "Logs: /tmp/wla-express.log  /tmp/wla-fastapi.log  /tmp/wla-vite.log"
log "Stop: ./scripts/stop.sh"
