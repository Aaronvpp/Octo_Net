#!/bin/bash
PIDFILE="./pidfile.pid"

if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null; then
        echo "Daemon is running with PID $PID"
    else
        echo "Daemon is not running (stale PID file)"
    fi
else
    echo "Daemon is not running"
fi