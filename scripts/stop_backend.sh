#!/usr/bin/env bash

PORT=9022

echo "Stopping backend on port ${PORT}"

PIDS=$(lsof -ti :"${PORT}" || true)

if [ -n "$PIDS" ]; then

    echo "$PIDS"

    kill -9 $PIDS

else

    echo "No backend process found"

fi


pkill -9 -f "backend.__main__:create_process_application" || true

pkill -9 -f "multiprocessing.spawn" || true

echo "Backend stopped"
