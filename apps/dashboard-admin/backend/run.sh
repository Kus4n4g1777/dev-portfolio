#!/bin/bash

# Wait for the PostgreSQL database to be ready
echo "Waiting for PostgreSQL..."
until pg_isready -h $POSTGRES_HOST -p 5432 -U $POSTGRES_USER; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready! Running migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8000

