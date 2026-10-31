#!/usr/bin/env bash
# Simple script to wait for PostgreSQL to accept connections.
# Usage: ./wait_for_db.sh
# Expects the following environment variables (default values match docker‑compose defaults):
#   POSTGRES_HOST (default: db)
#   POSTGRES_PORT (default: 5432)
#   POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB are not needed for the ping.

HOST=${POSTGRES_HOST:-db}
PORT=${POSTGRES_PORT:-5432}

# Try to connect every second, up to 30 attempts.
for i in {1..30}; do
    nc -z $HOST $PORT && exit 0
    echo "Waiting for PostgreSQL ($HOST:$PORT)... ($i)"
    sleep 1
done

echo "PostgreSQL did not become ready in time."
exit 1
