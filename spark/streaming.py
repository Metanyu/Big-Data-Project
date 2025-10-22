import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_avro


SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
SCHEMA_PATH = os.path.join(PROJECT_ROOT, "schemas", "taxi_trip.avsc")


# Load Avro schema as a string
with open(SCHEMA_PATH, "r") as f:
    avro_schema = f.read()


spark = SparkSession.builder \
    .appName("NYC Yellow Taxi Streaming") \
    .getOrCreate()


# Read stream from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "taxi-trips") \
    .load()


# Parse the Avro value from Kafka
parsed_df = df.select(
    from_avro(col("value"), avro_schema).alias("data")
).select("data.*")


# Transformations TODO: add transformations if needed


# Write stream to Cassandra TODO: Cassandra
query = parsed_df.writeStream \
    .format("org.apache.spark.sql.cassandra") \
    .option("keyspace", "") \
    .option("table", "") \
    .outputMode("append") \
    .start()

query.awaitTermination()