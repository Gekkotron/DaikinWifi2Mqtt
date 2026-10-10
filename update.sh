#!/bin/bash
set -e

cd "$(dirname "$0")"

SERVICE=daikin-mqtt-gateway

if docker compose version >/dev/null 2>&1; then
    DC=(docker compose)
else
    DC=(docker-compose)
fi

BEFORE=$(git rev-parse HEAD)
git pull --rebase
AFTER=$(git rev-parse HEAD)

# Is the service container already running?
RUNNING=$("${DC[@]}" ps -q "$SERVICE" 2>/dev/null)

if [ "$BEFORE" = "$AFTER" ] && [ -n "$RUNNING" ]; then
    echo "$(date): No changes and service already running, skipping rebuild."
    exit 0
fi

if [ "$BEFORE" = "$AFTER" ]; then
    echo "$(date): No code changes, but service is not running — starting it."
else
    echo "$(date): Changes detected ($BEFORE -> $AFTER), rebuilding..."
fi

"${DC[@]}" build --no-cache "$SERVICE"
"${DC[@]}" up -d "$SERVICE"

# Prune dangling images left over from --no-cache rebuilds.
docker image prune -f >/dev/null 2>&1 || true

echo "$(date): Update complete. Recent logs:"
"${DC[@]}" logs --tail=30 "$SERVICE"
