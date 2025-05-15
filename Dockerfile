# Dockerfile for Load Forecasting Webapp

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (like build-essential for some ML libraries if needed)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies from the main webapp
RUN pip install --no-cache-dir -r requirements.txt

# Install dependencies from the ML agents (Need to merge requirements or install separately)
# Assuming ML agent requirements are in a separate file for now
COPY /home/ubuntu/load_forecasting_agents/requirements.txt /app/ml_requirements.txt
RUN pip install --no-cache-dir -r /app/ml_requirements.txt

# Copy the entire web application source code
COPY ./src /app/src

# Copy the ML agent code into the container (adjust path if needed)
COPY /home/ubuntu/load_forecasting_agents /app/load_forecasting_agents

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variables (can be overridden in docker-compose)
ENV FLASK_APP=src.main:app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
# Set Python path to include the copied agents directory
ENV PYTHONPATH="/app:/app/load_forecasting_agents"
# Database connection details (can be set in docker-compose)
ENV DB_HOST=db
ENV DB_NAME=mydb
ENV DB_USERNAME=root
ENV DB_PASSWORD=password
ENV DB_PORT=3306
# Flask secret key (IMPORTANT: Change this in production/docker-compose)
ENV FLASK_SECRET_KEY="change_this_in_compose_file"

# Run the application using Flask's built-in server (for development/testing)
# For production, use a proper WSGI server like Gunicorn
CMD ["flask", "run"]
