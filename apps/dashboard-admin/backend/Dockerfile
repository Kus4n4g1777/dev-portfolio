# Use official Python image
FROM python:3.12-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy Alembic migrations
COPY alembic.ini .
COPY alembic ./alembic

# Copy app files
COPY . .

# Fix LF line endings for run.sh (Windows -> Linux)
RUN sed -i 's/\r$//' run.sh

# Make run.sh executable
RUN chmod +x run.sh

# Expose port
EXPOSE 8000

# Default command
CMD ["./run.sh"]
