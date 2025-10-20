import polars as pl
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import StringSerializer
import os

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

SCHEMA_PATH = os.path.join(PROJECT_ROOT, "schemas", "taxi_trip.avsc")
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "yellow_tripdata_2025-08.parquet")
TOPIC_NAME = "taxi-trips"
SCHEMA_REGISTRY_URL = "http://localhost:8081"

# 1. Load the Avro schema from the .avsc file
try:
    with open(SCHEMA_PATH, "r") as f:
        schema_str = f.read()
except FileNotFoundError:
    print(f"ERROR: Schema file not found at {SCHEMA_PATH}")
    exit(1)
if not schema_str:
    print(f"ERROR: Schema file at {SCHEMA_PATH} is empty.")
    exit(1)

# 2. Set up Schema Registry client
schema_registry_conf = {'url': SCHEMA_REGISTRY_URL}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# 3. Define serializers for key and value
string_serializer = StringSerializer('utf_8')

# --- THIS IS THE FIX ---
# The arguments were swapped. It must be (client, schema_str).
avro_serializer = AvroSerializer(schema_registry_client,
                                 schema_str,
                                 to_dict=None)
# ------------------------

# 4. Update the producer configuration
producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'key.serializer': string_serializer,
    'value.serializer': avro_serializer
}

# 5. Use SerializingProducer
producer = SerializingProducer(producer_config)

print(f"Reading Parquet file from {DATA_PATH}...")
try:
    trips = pl.read_parquet(DATA_PATH)
except FileNotFoundError:
    print(f"ERROR: Data file not found at {DATA_PATH}")
    exit(1)

trips_subset = trips.select(["VendorID", "passenger_count", "total_amount"])
print("File read successfully. Starting to stream AVRO data...")

# 6. Iterate and produce records
for row in trips_subset.to_dicts():
    try:
        producer.produce(topic=TOPIC_NAME, value=row, key=str(row['VendorID']))
        producer.poll(0)
    except BufferError:
        print("Buffer full, flushing...")
        producer.flush()
    except Exception as e:
        print(f"An error occurred: {e}")
        producer.flush()

print("Finished streaming all data. Flushing final messages...")
producer.flush()