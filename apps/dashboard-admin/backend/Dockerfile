# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install the PostgreSQL client tools for pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the Alembic configuration and migration scripts
# This is crucial for the migrations to run correctly
COPY alembic.ini .
COPY alembic ./alembic

# Copy only what we need, nothing more
# This ensures Alembic can find your models
COPY run.sh /app/run.sh
RUN chmod +x /app/run.sh


# Expose the port the app runs on
EXPOSE 8000

# Set the startup script as the command
CMD ["./run.sh"]
