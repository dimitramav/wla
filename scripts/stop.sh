#!/usr/bin/env bash
# stop.sh — Kill all WLA services started by start.sh

PIDS_FILE="/tmp/wla.pids"

if [[ ! -f "$PIDS_FILE" ]]; then
  echo "[wla] No PID file found — nothing to stop"
  exit 0
fi

while read -r name pid; do
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" && echo "[wla] Stopped $name (pid $pid)"
  else
    echo "[wla] $name (pid $pid) was already stopped"
  fi
done < "$PIDS_FILE"

rm -f "$PIDS_FILE"
echo "[wla] Done"
