import polars as pl
import json
from confluent_kafka import Producer
import time

# Kafka producer configuration
p = Producer({
    "bootstrap.servers": "localhost:9092",
    "enable.idempotence": True # Ensures messages are not duplicated
})

# Kafka topic
TOPIC_NAME = "taxi_trips"

# Load the dataset
print("Reading Parquet file...")
trips = pl.read_parquet("kafka/yellow_tripdata_2025-08.parquet")
print("File read successfully. Starting to stream data...")

# Iterate over each row and send it to Kafka
for row in trips.iter_rows(named=True):
    try:
        # Convert row to JSON string - Kafka messages are key/value pairs
        # We'll use the vendor ID as the key and the full row as the value
        key = str(row['VendorID'])
        value = json.dumps(row, default=str) # Use default=str for datetime objects

        # Produce the message
        p.produce(TOPIC_NAME, key=key.encode('utf-8'), value=value.encode('utf-8'))

        # p.poll(0) is required for triggering delivery callbacks
        p.poll(0)

        print(f"Produced message with key '{key}': {value}")

        # Simulate a real-time stream by waiting a bit
        time.sleep(0.1)

    except BufferError:
        print(f"Local producer queue is full ({len(p)} messages awaiting delivery): flushing...")
        p.flush()
    except Exception as e:
        print(f"An error occurred: {e}")

print("Finished streaming all data. Flushing final messages...")
# Wait for any outstanding messages to be delivered and delivery reports received.
p.flush()