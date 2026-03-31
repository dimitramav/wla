#!/usr/bin/env bash
# start-browser.sh — Start headless Chromium with CDP port 9222 for agent UI testing

if curl -sSf http://localhost:9222/json/version >/dev/null 2>&1; then
  echo "[wla] Headless Chrome is already running on port 9222"
else
  echo "[wla] Starting headless Chrome on port 9222..."
  nohup /usr/bin/chromium-browser --headless --no-sandbox --remote-debugging-port=9222 > /tmp/chrome.log 2>&1 &
  sleep 2
  if curl -sSf http://localhost:9222/json/version >/dev/null 2>&1; then
    echo "[wla] Chrome is UP"
  else
    echo "[wla] ERROR: Chrome failed to start"
    exit 1
  fi
fi
