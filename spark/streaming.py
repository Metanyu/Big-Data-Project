import os
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, avg, sum as spark_sum, count,
    when, lit, hour, dayofweek, unix_timestamp, broadcast
)
from pyspark.sql.types import (
    StructType, StructField, IntegerType, LongType,
    DoubleType, TimestampType, StringType
)

# ---------- Logging Setup ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Config ----------
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "taxi-trips")
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "taxi_streaming")
CHECKPOINT_ROOT = os.getenv("CHECKPOINT_ROOT", "/tmp/spark_checkpoints")

# 7ax1 z0n3 100kup from: https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
ZONE_LOOKUP_PATH = os.path.join(PROJECT_ROOT, "spark", "taxi_zone_lookup.csv")

# ---------- Schemas ----------
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

# ---------- Spark Session ----------
spark = (
    SparkSession.builder
    .appName("NYC Taxi Trip Streaming Pipeline")
    .config("spark.cassandra.connection.host", CASSANDRA_HOST)
    .config("spark.cassandra.connection.port", "9042")
    .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_ROOT)
    .master("local[*]")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# ---------- Read from Kafka ----------
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "latest") 
    .load()
)

parsed_df = kafka_df.select(
    from_json(col("value").cast("string"), taxi_schema).alias("data"),
    col("timestamp").alias("kafka_timestamp")
).select("data.*", "kafka_timestamp")

# ---------- Feature Engineering ----------
# 1. Basic Cleaning & Durations
df_processed = parsed_df.withColumn(
    "trip_duration_sec", 
    (unix_timestamp("tpep_dropoff_datetime") - unix_timestamp("tpep_pickup_datetime"))
).filter(
    (col("trip_distance") > 0) & (col("trip_distance") < 500) &
    (col("passenger_count") > 0) & (col("total_amount") > 0) &
    (col("trip_duration_sec") > 60) & (col("trip_duration_sec") < 14400)
)

# 2. Event Time & Metrics
df_enriched = df_processed.withColumn(
    "event_time",
    when(col("tpep_pickup_datetime").isNotNull(), col("tpep_pickup_datetime"))
    .otherwise(col("kafka_timestamp"))
).withWatermark("event_time", "10 minutes") \
.withColumn("pickup_hour", hour("event_time")) \
.withColumn("pickup_weekday", dayofweek("event_time")) \
.withColumn(
    "speed_mph",
    when(col("trip_duration_sec") > 0, (col("trip_distance") / (col("trip_duration_sec") / 3600)))
    .otherwise(lit(0.0))
).withColumn(
    "fare_per_mile",
    when(col("trip_distance") > 0, (col("fare_amount") / col("trip_distance")))
    .otherwise(lit(0.0))
).withColumn(
    "tip_ratio",
    when(col("total_amount") > 0, (col("tip_amount") / col("total_amount")))
    .otherwise(lit(0.0))
).withColumn(
    "is_weekend", 
    col("pickup_weekday").isin([1, 7]) # 1=Sun, 7=Sat
).withColumn(
    "peak_category",
    when((~col("is_weekend")) & (col("pickup_hour").between(16, 19)), lit("PM Rush"))
    .when((~col("is_weekend")) & (col("pickup_hour").between(7, 9)) , lit("AM Rush"))
    .otherwise(lit("Off-Peak"))
).withColumn(
    "payment_desc",
    when(col("payment_type") == 1, "Credit Card")
    .when(col("payment_type") == 2, "Cash")
    .otherwise("Other")
)

# 3. Zone Lookup Join
try:
    zone_df = spark.read.option("header", "true").option("inferSchema", "true").csv(ZONE_LOOKUP_PATH)
    zone_lookup = zone_df.select(
        col("LocationID").cast("int").alias("lookup_id"),
        col("Zone").alias("pickup_zone")
    )
    
    final_stream = df_enriched.join(
        broadcast(zone_lookup),
        df_enriched.PULocationID == zone_lookup.lookup_id,
        "left"
    ).drop("lookup_id").fillna({"pickup_zone": "Unknown"})
except Exception as e:
    logger.warning(f"Zone lookup failed: {e}")
    final_stream = df_enriched.withColumn("pickup_zone", lit("Unknown"))


# ---------- Modular Aggregation Logic ----------

def get_zone_agg(df, interval):
    """Returns dataframe grouped by Zone + Time Window"""
    return df \
        .groupBy(window(col("event_time"), interval), col("pickup_zone")) \
        .agg(
            count("*").alias("total_trips"),
            spark_sum("total_amount").alias("total_revenue"),
            avg("fare_per_mile").alias("avg_fare_per_mile"),
            avg("speed_mph").alias("avg_speed_mph"),
            avg("trip_duration_sec").alias("avg_duration_sec")
        ).select(
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            "pickup_zone", "total_trips", "total_revenue", 
            "avg_fare_per_mile", "avg_speed_mph", "avg_duration_sec"
        )

def get_global_agg(df, interval):
    """Returns dataframe grouped by Time Window only"""
    return df \
        .groupBy(window(col("event_time"), interval)) \
        .agg(
            count("*").alias("total_trips"),
            spark_sum("total_amount").alias("total_revenue"),
            avg("speed_mph").alias("avg_speed_mph"),
            avg("tip_ratio").alias("avg_tip_ratio")
        ).withColumn("shard_id", lit("1")) \
        .select(
            "shard_id",
            col("window.start").alias("window_start"),
            col("window.end").alias("window_end"),
            "total_trips", "total_revenue", "avg_speed_mph", "avg_tip_ratio"
        )

def get_peak_agg(df, interval):
    """Returns dataframe grouped by Peak Category"""
    return df \
        .groupBy(window(col("event_time"), interval), col("peak_category")) \
        .agg(count("*").alias("total_trips")) \
        .select(col("window.start").alias("window_start"), "peak_category", "total_trips")

def get_payment_agg(df, interval):
    """Returns dataframe grouped by Payment Type"""
    return df \
        .groupBy(window(col("event_time"), interval), col("payment_desc").alias("payment_type")) \
        .agg(
            count("*").alias("total_trips"),
            avg("tip_ratio").alias("avg_tip_ratio")
        ).select(col("window.start").alias("window_start"), "payment_type", "total_trips", "avg_tip_ratio")


# ---------- Stream Sinks & Execution Loop ----------

def write_cassandra(df, epoch_id, table):
    if df.rdd.isEmpty():
        return
    logger.info(f"Writing batch {epoch_id} to {table}")
    df.write \
        .format("org.apache.spark.sql.cassandra") \
        .mode("append") \
        .options(table=table, keyspace=CASSANDRA_KEYSPACE) \
        .save()

# List of desired streams: (Type, Interval, Table Suffix)
stream_configs = [
    # 1. ZONE PERFORMANCE: 5m and 1h
    ("zone", "5 minutes", "_5m"),
    ("zone", "1 hour", "_1h"),
    
    # 2. GLOBAL KPIs: 5m and 1h
    ("global", "5 minutes", "_5m"),
    ("global", "1 hour", "_1h"),

    # 3. PEAK & PAYMENT: 15m only
    ("peak", "15 minutes", "_15m"),
    ("payment", "15 minutes", "_15m")
]

streams = []
print("Initializing Streams...")

for stream_type, interval, suffix in stream_configs:
    
    # 1. Generate the DataFrame based on type
    if stream_type == "zone":
        agg_df = get_zone_agg(final_stream, interval)
        base_table = "zone_performance"
    elif stream_type == "global":
        agg_df = get_global_agg(final_stream, interval)
        base_table = "global_kpis"
    elif stream_type == "peak":
        agg_df = get_peak_agg(final_stream, interval)
        base_table = "peak_analysis"
    elif stream_type == "payment":
        agg_df = get_payment_agg(final_stream, interval)
        base_table = "payment_analysis"
    else:
        continue

    # 2. Define Table and Checkpoint
    full_table_name = f"{base_table}{suffix}"
    # CRITICAL: Unique checkpoint per stream type AND interval
    checkpoint_name = f"{stream_type}{suffix}" 
    checkpoint_path = os.path.join(CHECKPOINT_ROOT, checkpoint_name)

    # 3. Start Stream
    query = agg_df.writeStream \
        .outputMode("update") \
        .foreachBatch(lambda df, id, t=full_table_name: write_cassandra(df, id, t)) \
        .option("checkpointLocation", checkpoint_path) \
        .trigger(processingTime='10 seconds') \
        .start()
    
    streams.append(query)
    print(f"Started {stream_type.upper()} stream [{interval}] -> Table: {full_table_name}")

print(f"Total streams running: {len(streams)}")
spark.streams.awaitAnyTermination()