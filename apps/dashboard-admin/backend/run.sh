#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Debug: print env variables
echo "DB_USER=$DB_USER"
echo "DB_NAME=$DB_NAME"
echo "DB_HOST=$DB_HOST"
echo "DB_PASSWORD=${DB_PASSWORD:+******}"  # hide password


# Ensure env variables exist
: "${DB_HOST:?Need to set DB_HOST}"
: "${DB_USER:?Need to set DB_USER}"
: "${DB_PASSWORD:?Need to set DB_PASSWORD}"
: "${DB_NAME:?Need to set DB_NAME}"

export PGPASSWORD=$DB_PASSWORD  # For pg_isready and psql

echo "Waiting for PostgreSQL at $DB_HOST..."
until pg_isready -h "$DB_HOST" -p 5432 -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready! Running migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000

