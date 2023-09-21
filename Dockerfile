# Use the official Python image as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

COPY bill.py /app/
COPY app.py /app/
COPY gunicorn_config.py /app/
COPY bills.db /app/

# Install any dependencies
RUN pip install Flask lxml requests gunicorn

# Expose a port if your Flask app listens on one gunicorn_config.py
EXPOSE 5001

# Run your Flask app using Gunicorn with the specified configuration
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
