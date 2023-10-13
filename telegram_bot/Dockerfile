# Use the official Python image as a parent image
FROM python:3.11.6-alpine3.18
# Set the working directory in the container
WORKDIR /app

COPY ./telegram_bot /app/bot
COPY ./billdb /app/package/billdb
COPY ./setup.py /app/package/setup.py

# Install any dependencies
RUN pip install ./package[telegram]

# Run your Flask app using Gunicorn with the specified configuration
CMD ["python", "./bot/_telegram-bot.py"]
