# Use the official Python image as the base image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app/

# Copy the requirements file into the container
COPY requirements.txt .


# Copy the Django project code into the container
COPY . .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt