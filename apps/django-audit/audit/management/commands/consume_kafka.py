from django.core.management.base import BaseCommand
from confluent_kafka import Consumer
import json
import os
from audit.models import AuditLog

class Command(BaseCommand):
    def handle(self, *args, **options):
        conf = {
            'bootstrap.servers': os.environ.get('KAFKA_BROKERS', 'kafka:9092'),
            'group.id': 'django-audit-group',
            'auto.offset.reset': 'earliest'
        }
        consumer = Consumer(conf)
        topic = os.environ.get('KAFKA_TOPIC', 'llm.inference.events')
        consumer.subscribe([topic])

        print(f"⚡ Listening to Kafka topic: {topic}")
        while True:
            msg = consumer.poll(1.0)
            if msg is None: continue
            if msg.error(): continue

            try:
                data = json.loads(msg.value().decode('utf-8'))
                AuditLog.objects.create(
                    event_type=data.get('type', 'system_event'),
                    payload=data
                )
                print(f"Logged: {data.get('type')}")
            except Exception as e:
                print(f"Error: {e}")
