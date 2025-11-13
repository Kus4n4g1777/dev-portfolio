# Use the official AWS base image for Python 3.9
FROM public.ecr.aws/lambda/python:3.9

# Copy the requirements file
COPY requirements.txt .

# Install the boto3 library
RUN pip install -r requirements.txt

# --- This is the CHANGE ---
# Copy the *entire* 'src' folder into the container
COPY src/ ${LAMBDA_TASK_ROOT}
# --- End of CHANGE ---

# --- This is the 2nd CHANGE ---
# Point to the *new* handler path: {filename}.{function_name}
CMD ["handler.login_logger"]
# --- End of CHANGE ---