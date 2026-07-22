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

# Copy source code
COPY ./app /app

# Expose FastAPI port
EXPOSE 8003

# Run FastAPI agent API
CMD ["uvicorn", "main_api:api", "--host", "0.0.0.0", "--port", "8003", "--reload"]
