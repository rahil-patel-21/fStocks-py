# Use the official Ubuntu image with specified platform as a base image
FROM --platform=linux/amd64 ubuntu:20.04

# Prevent prompts during package installation
ARG DEBIAN_FRONTEND=noninteractive

# Update the package list and install dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.9 \
    python3.9-venv \
    python3.9-dev \
    python3-pip \
    && apt-get clean

# Set up a virtual environment
RUN python3.9 -m venv /opt/venv

# Make sure scripts in the virtualenv are usable
ENV PATH="/opt/venv/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make port 80 available to the world outside this container
EXPOSE 8008

# Run app.py when the container launches
CMD ["python", "app.py"]