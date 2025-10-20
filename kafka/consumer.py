# src/consumer.py (Updated)

from confluent_kafka import DeserializingConsumer
from confluent_kafka.avro.serializer import SerializerError
from confluent_kafka.serialization import StringDeserializer
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.schema_registry import SchemaRegistryClient
import os

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "schemas", "taxi_trip.avsc")

# 1. Load the Avro schema to be used by the deserializer
with open(SCHEMA_PATH, "r") as f:
    schema_str = f.read()
SCHEMA_REGISTRY_URL = "http://localhost:8081"
schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)
# 2. Define deserializers for key and value
#    The key is a plain string, the value is Avro
key_deserializer = StringDeserializer('utf_8')
avro_deserializer = AvroDeserializer(schema_registry_client, schema_str)

# 3. Update the consumer configuration
consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'key.deserializer': key_deserializer,
    'value.deserializer': avro_deserializer, # Use the Avro deserializer for the value
    'group.id': 'taxi-avro-consumer-group-2', # Changed group.id for a clean start
    'auto.offset.reset': 'earliest',
    # No need for schema.registry.url here, AvroDeserializer handles it if needed,
    # but it's often included for clarity.
    # 'schema.registry.url': 'http://localhost:8081'
}

# 4. Use DeserializingConsumer instead of AvroConsumer
consumer = DeserializingConsumer(consumer_config)
consumer.subscribe(['taxi-trips'])

print("Modern AVRO Consumer started. Waiting for messages...")

try:
    while True:
        try:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue
            
            value = msg.value()
            print(f"Received message: key='{msg.key()}', value={value}")

        except SerializerError as e:
            print(f"Message deserialization failed: {e}")
except KeyboardInterrupt:
    print("Stopping consumer.")
finally:
    consumer.close()