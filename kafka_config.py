from aiokafka import AIOKafkaProducer
import json
import os
from dotenv import load_dotenv

load_dotenv()

bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
if not bootstrap_servers:
    raise ValueError("KAFKA_BOOTSTRAP_SERVERS not configured in .env file")

# Productor global
kafka_producer = None

async def start_kafka():
    global kafka_producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    await kafka_producer.start()

async def stop_kafka():
    await kafka_producer.stop()

async def publish_event(topic: str, event: dict):
    await kafka_producer.send(topic, event)