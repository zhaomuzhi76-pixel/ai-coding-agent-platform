#!/usr/bin/env bash

set -e

PORT=4173

echo "===== FRONTEND PREVIEW START ====="
echo "CHECK PORT: ${PORT}"

PID=$(lsof -ti:${PORT} || true)

if [ -n "$PID" ]; then
    echo "PORT ${PORT} USED BY PID=${PID}"
    echo "STOPPING OLD PREVIEW PROCESS..."

    kill -9 $PID || true

    sleep 1
fi

echo "PORT ${PORT} READY"

echo "BUILD CHECK..."
npm run build

echo "START VITE PREVIEW..."
npm exec vite preview -- --host 0.0.0.0 --port ${PORT}
