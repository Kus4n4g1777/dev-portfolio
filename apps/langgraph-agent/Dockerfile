# We use a official version from Python
FROM python:3.11-slim

# Avoid Python to overwrite .pyc files and force real time log
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory at the container
WORKDIR /app

# Install necesary dependencies from the system when compiling psycopg2 (PostgreSQL)
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar source code
COPY ./app /app

# Default command to keep the container alive while we develop
CMD ["tail", "-f", "/dev/null"]
