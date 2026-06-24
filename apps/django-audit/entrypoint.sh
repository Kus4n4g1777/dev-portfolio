#!/bin/bash
# We initialize the database tables
python manage.py makemigrations audit
python manage.py migrate

# We start the Kafka consumer in the background
python manage.py consume_kafka &

# We start the web server for the healthcheck and GraphQL gateway
exec python manage.py runserver 0.0.0.0:8000
