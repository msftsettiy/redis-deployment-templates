# Use an official Python image as the base
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY frontdoor.py .

RUN mkdir -p /app/certs

# Copy the certs used to authenticate with confidential ledger
COPY admin_cert.pem /app/certs/
COPY admin_privk.pem /app/certs/

# Expose the port your app runs on
EXPOSE 5000

# Command to run the web server
CMD ["python", "frontdoor.py"]