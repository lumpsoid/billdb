# Use the official Python image as a parent image
FROM python:3.11.6-alpine3.18

# Set the working directory in the container
WORKDIR /app

COPY ./api/app.py /app/
COPY ./api/gunicorn_config.py /app/
COPY ./billdb /app/package/billdb
COPY ./setup.py /app/package/setup.py

# Install any dependencies
RUN pip install ./package[api]

RUN touch ./flask.log

# Expose a port if your Flask app listens on one gunicorn_config.py
EXPOSE 5001

# Run your Flask app using Gunicorn with the specified configuration
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]
