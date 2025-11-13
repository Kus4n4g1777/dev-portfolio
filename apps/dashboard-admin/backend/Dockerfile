# 1️⃣ Build & Test stage
FROM python:3.11 AS build
WORKDIR /app

# Install dev dependencies (pytest, etc.)
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Install prod dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all app code
COPY . .

# 💥 RUN PYTEST 💥
# This will find and run all your tests
RUN pytest

# 2️⃣ Runtime stage
FROM python:3.11-slim
WORKDIR /app

# Install ONLY production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Install Postgres client & curl
RUN apt-get update && apt-get install -y postgresql-client curl && rm -rf /var/lib/apt/lists/*

# Copy Alembic migrations
COPY alembic.ini .
COPY alembic ./alembic

# Copy app files (we copy from context, not stage 1)
COPY . .

# Fix LF line endings for run.sh
RUN sed -i 's/\r$//' run.sh

# Make run.sh executable
RUN chmod +x run.sh

# Expose port
EXPOSE 8000

# Default command
CMD ["./run.sh"]