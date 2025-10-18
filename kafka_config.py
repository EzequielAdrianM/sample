from aiokafka import AIOKafkaProducer
import json

# Productor global
kafka_producer = None

async def start_kafka():
    global kafka_producer
    kafka_producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    await kafka_producer.start()

async def stop_kafka():
    await kafka_producer.stop()

async def publish_event(topic: str, event: dict):
    await kafka_producer.send(topic, event)