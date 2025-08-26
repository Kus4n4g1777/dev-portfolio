  # Use an official Python runtime as a parent image
    # We're using a specific version for consistency.
    FROM python:3.11-slim

    # Set the working directory in the container
    WORKDIR /app

    # Copy the requirements file into the container
    # We copy this first to leverage Docker's build cache.
    COPY ./requirements.txt /app/requirements.txt

    # Install any dependencies
    RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

    # Copy the rest of the application code into the container
    COPY . /app

    # Expose the port the app runs on
    EXPOSE 8000

    # Define the command to run the application
    # We use the Gunicorn/Uvicorn pattern for production-ready deployments.
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
