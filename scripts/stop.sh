#!/usr/bin/env bash
# stop.sh — Kill all WLA services started by start.sh

PIDS_FILE="/tmp/wla.pids"
WLA_PORTS=(3001 8000 5173)

kill_pid_tree() {
  local pid="$1"
  # Kill descendants first (nodemon → sh -c → node src/server.js)
  local kids
  kids=$(pgrep -P "$pid" 2>/dev/null || true)
  for kid in $kids; do
    kill_pid_tree "$kid"
  done
  kill "$pid" 2>/dev/null || true
}

# 1. Kill PIDs recorded by start.sh (and their descendants)
if [[ -f "$PIDS_FILE" ]]; then
  while read -r name pid; do
    if kill -0 "$pid" 2>/dev/null; then
      kill_pid_tree "$pid"
      echo "[wla] Stopped $name (pid $pid)"
    else
      echo "[wla] $name (pid $pid) was already stopped"
    fi
  done < "$PIDS_FILE"
  rm -f "$PIDS_FILE"
else
  echo "[wla] No PID file found — sweeping ports only"
fi

# 2. Port sweep — catch orphaned processes (e.g. node children that survived
#    when their nodemon parent was killed and they got reparented to init)
sleep 1
for port in "${WLA_PORTS[@]}"; do
  pids=$(ss -ltnpH "sport = :$port" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | sort -u)
  for pid in $pids; do
    echo "[wla] Killing orphan on port $port (pid $pid)"
    kill_pid_tree "$pid"
  done
done

# 3. Force-kill anything still bound after grace period
sleep 1
for port in "${WLA_PORTS[@]}"; do
  pids=$(ss -ltnpH "sport = :$port" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | sort -u)
  for pid in $pids; do
    echo "[wla] SIGKILL pid $pid (port $port still bound)"
    kill -9 "$pid" 2>/dev/null || true
  done
done

echo "[wla] Done"
