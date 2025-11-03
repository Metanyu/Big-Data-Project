# spark/stream_pipeline.py
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, avg, sum as spark_sum, count,
    current_timestamp, when, lit
)
from pyspark.sql.types import (
    StructType, StructField, IntegerType, LongType,
    DoubleType, TimestampType, StringType
)

# ---------- Config ----------
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "taxi-trips")
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "taxi_streaming")

CHECKPOINT_ROOT = os.getenv("CHECKPOINT_ROOT", "/tmp/spark_checkpoints")
os.makedirs(CHECKPOINT_ROOT, exist_ok=True)
CHECKPOINT_WINDOWED = os.path.join(CHECKPOINT_ROOT, "windowed")
CHECKPOINT_HOURLY = os.path.join(CHECKPOINT_ROOT, "hourly")

# ---------- Schema ----------
# Define schema for incoming JSON messages (matching producer output)
taxi_schema = StructType([
    StructField("VendorID", IntegerType(), True),
    StructField("tpep_pickup_datetime", TimestampType(), True),
    StructField("tpep_dropoff_datetime", TimestampType(), True),
    StructField("passenger_count", LongType(), True),
    StructField("trip_distance", DoubleType(), True),
    StructField("RatecodeID", LongType(), True),
    StructField("store_and_fwd_flag", StringType(), True),
    StructField("PULocationID", IntegerType(), True),
    StructField("DOLocationID", IntegerType(), True),
    StructField("payment_type", LongType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("extra", DoubleType(), True),
    StructField("mta_tax", DoubleType(), True),
    StructField("tip_amount", DoubleType(), True),
    StructField("tolls_amount", DoubleType(), True),
    StructField("improvement_surcharge", DoubleType(), True),
    StructField("total_amount", DoubleType(), True),
    StructField("congestion_surcharge", DoubleType(), True),
    StructField("Airport_fee", DoubleType(), True),
    StructField("cbd_congestion_fee", DoubleType(), True)
])

# ---------- Spark session ----------
spark = (
    SparkSession.builder
    .appName("NYC Taxi Trip Streaming Pipeline")
    # Usually supply connector jars via spark-submit --packages
    .config("spark.cassandra.connection.host", CASSANDRA_HOST)
    .config("spark.cassandra.connection.port", "9042")
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_ROOT)
    .config("spark.sql.adaptive.enabled", "false")
    .master("local[*]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# Fine-tune for local dev
spark.conf.set("spark.sql.shuffle.partitions", "4")  # tune for local tests

# ---------- Read from Kafka ----------
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

parsed_df = kafka_df.select(
    from_json(col("value").cast("string"), taxi_schema).alias("data"),
    col("timestamp").alias("kafka_timestamp")
).select("data.*", "kafka_timestamp")

# print schema (do not wrap with print())
parsed_df.printSchema()

# ---------- event time ----------
df_with_event_time = parsed_df.withColumn(
    "event_time",
    when(col("tpep_pickup_datetime").isNotNull(), col("tpep_pickup_datetime"))
    .otherwise(col("kafka_timestamp"))
)

watermarked = df_with_event_time.withWatermark("event_time", "10 minutes")

# ---------- distance category (avoid Python UDF for perf) ----------
distance_category = when(col("trip_distance").isNull(), lit("unknown")) \
    .when(col("trip_distance") < 2.0, lit("short")) \
    .when(col("trip_distance") < 10.0, lit("medium")) \
    .otherwise(lit("long"))

enriched = watermarked.withColumn("distance_category", distance_category)

# ---------- windowed aggregation ----------
windowed_agg = (
    enriched
    .groupBy(window(col("event_time"), "5 minutes"), col("VendorID"))
    .agg(
        count("*").alias("trip_count"),
        avg("passenger_count").alias("avg_passenger_count"),
        spark_sum("total_amount").alias("total_revenue"),
        avg("fare_amount").alias("avg_fare")
    )
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("VendorID").alias("vendor_id"),
        "trip_count", "avg_passenger_count", "total_revenue", "avg_fare"
    )
)

# ---------- foreachBatch writer to Cassandra ----------
def write_to_cassandra(batch_df, batch_id, keyspace=CASSANDRA_KEYSPACE, table="trip_aggregations_5min"):
    if batch_df.rdd.isEmpty():
        return
    # Optionally repartition to number of Cassandra nodes or to avoid too many connections
    batch_df = batch_df.repartition(4)
    (batch_df
        .write
        .format("org.apache.spark.sql.cassandra")
        .mode("append")
        .options(table=table, keyspace=keyspace)
        .save()
    )

query_windowed = (
    windowed_agg.writeStream
    .outputMode("update")             # update is okay for windowed agg; foreachBatch handles writes
    .foreachBatch(lambda df, epochId: write_to_cassandra(df, epochId, table="trip_aggregations_5min"))
    .option("checkpointLocation", CHECKPOINT_WINDOWED)
    .start()
)

# ---------- hourly aggregation ----------
hourly_agg = (
    enriched
    .groupBy(window(col("event_time"), "1 hour"))
    .agg(
        count("*").alias("total_trips"),
        spark_sum("total_amount").alias("total_revenue"),
        avg("passenger_count").alias("avg_passengers")
    )
    .select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        "total_trips", "total_revenue", "avg_passengers"
    )
)

query_hourly = (
    hourly_agg.writeStream
    .outputMode("update")
    .foreachBatch(lambda df, epochId: write_to_cassandra(df, epochId, table="trip_aggregations_hourly"))
    .option("checkpointLocation", CHECKPOINT_HOURLY)
    .start()
)

# ---------- start ----------
print("Streaming queries started...")
query_windowed.awaitTermination()
