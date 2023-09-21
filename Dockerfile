# Use the official Python image as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy your Python script into the container
COPY bill.py /app/

# Copy your Gunicorn configuration file into the container
COPY gunicorn_config.py /app/

# Install any dependencies your script requires
RUN pip install Flask lxml requests gunicorn

# Copy your SQLite database file into the container
COPY bills.db /app/

# Expose a port if your Flask app listens on one (optional)
EXPOSE 5001

# Run your Flask app using Gunicorn with the specified configuration
CMD ["gunicorn", "--config", "config.py", "your_script:app"]
