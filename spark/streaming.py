import os
import sys
import logging
import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, avg, sum as spark_sum, count,
    when, lit, hour, dayofweek, unix_timestamp, broadcast, to_date
)
from pyspark.sql.types import (
    StructType, StructField, IntegerType, LongType,
    DoubleType, TimestampType, StringType
)

# ---------- Config ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "broker:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "taxi-trips")
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "taxi_streaming")
CHECKPOINT_ROOT = os.getenv("CHECKPOINT_ROOT", "/tmp/spark_checkpoints")

# HDFS Config
HDFS_NAMENODE = os.getenv("HDFS_NAMENODE", "hdfs://namenode:9000")
HDFS_PATH = f"{HDFS_NAMENODE}/taxi_data/raw"

# 7ax1 z0n3 100kup from: https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
SCRIPT_DIR = os.path.dirname(__file__)
ZONE_LOOKUP_PATH = os.path.join(SCRIPT_DIR, "taxi_zone_lookup.csv")

# ---------- Schema ----------
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

# ---------- 1. Initialization Helper ----------
def get_spark_session(mode):
    builder = SparkSession.builder \
        .appName(f"NYC Taxi Lambda [{mode.upper()}]") \
        .config("spark.cassandra.connection.host", CASSANDRA_HOST) \
        .config("spark.cassandra.connection.port", "9042") \
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_ROOT) \
        .config("spark.network.timeout", "600s") \
        .config("spark.executor.heartbeatInterval", "120s")
    
    return builder.master("local[2]").getOrCreate()

# ---------- 2. Data Reader Helper ----------
def read_kafka(spark):
    logger.info("Initializing Kafka ReadStream...")
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()

# ---------- 3. Unified Processing Logic ----------
def process_data(df, spark):
    # Parse JSON
    parsed_df = df.select(
        from_json(col("value").cast("string"), taxi_schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")
    ).select("data.*", "kafka_timestamp")

    # Basic Feature Engineering
    df_processed = parsed_df.withColumn(
        "trip_duration_sec", 
        (unix_timestamp("tpep_dropoff_datetime") - unix_timestamp("tpep_pickup_datetime"))
    ).filter(
        (col("trip_distance") > 0) & (col("trip_distance") < 500) &
        (col("passenger_count") > 0) & (col("total_amount") > 0) &
        (col("trip_duration_sec") > 60) & (col("trip_duration_sec") < 14400)
    )

    df_enriched = df_processed.withColumn(
        "event_time",
        when(col("tpep_pickup_datetime").isNotNull(), col("tpep_pickup_datetime"))
        .otherwise(col("kafka_timestamp"))
    ).withColumn(
        "event_date", 
        to_date(col("event_time")) # Partition key cho HDFS
    )

    # Watermark cho Aggregation
    df_enriched = df_enriched.withWatermark("event_time", "2 hours")

    # Metrics Calculation
    df_final = df_enriched.withColumn("pickup_hour", hour("event_time")) \
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
            col("pickup_weekday").isin([1, 7])
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

    # Zone Lookup (Broadcast Join)
    try:
        zone_df = spark.read.option("header", "true").option("inferSchema", "true").csv(ZONE_LOOKUP_PATH)
        zone_lookup = zone_df.select(col("LocationID").cast("int").alias("lid"), col("Zone").alias("pickup_zone"))
        df_final = df_final.join(broadcast(zone_lookup), df_final.PULocationID == zone_lookup.lid, "left") \
            .drop("lid").fillna({"pickup_zone": "Unknown"})
    except Exception as e:
        logger.warning(f"Zone lookup failed: {e}")
        df_final = df_final.withColumn("pickup_zone", lit("Unknown"))
        
    return df_final

# ---------- 4. Aggregation Functions (Speed Layer) ----------
def get_zone_agg(df, interval):
    return df.groupBy(window(col("event_time"), interval), col("pickup_zone")).agg(
        count("*").alias("total_trips"),
        spark_sum("total_amount").alias("total_revenue"),
        avg("fare_per_mile").alias("avg_fare_per_mile"),
        avg("speed_mph").alias("avg_speed_mph"),
        avg("trip_duration_sec").alias("avg_duration_sec")
    ).select(col("window.start").alias("window_start"), col("window.end").alias("window_end"), "pickup_zone", "total_trips", "total_revenue", "avg_fare_per_mile", "avg_speed_mph", "avg_duration_sec")

def get_global_agg(df, interval):
    return df.groupBy(window(col("event_time"), interval)).agg(
        count("*").alias("total_trips"),
        spark_sum("total_amount").alias("total_revenue"),
        avg("speed_mph").alias("avg_speed_mph"),
        avg("tip_ratio").alias("avg_tip_ratio")
    ).withColumn("shard_id", lit("1")).select("shard_id", col("window.start").alias("window_start"), col("window.end").alias("window_end"), "total_trips", "total_revenue", "avg_speed_mph", "avg_tip_ratio")

def get_peak_agg(df, interval):
    return df.groupBy(window(col("event_time"), interval), col("peak_category")).agg(
        count("*").alias("total_trips")
    ).select(col("window.start").alias("window_start"), "peak_category", "total_trips")

def get_payment_agg(df, interval):
    return df.groupBy(window(col("event_time"), interval), col("payment_desc").alias("payment_type")).agg(
        count("*").alias("total_trips"), avg("tip_ratio").alias("avg_tip_ratio")
    ).select(col("window.start").alias("window_start"), "payment_type", "total_trips", "avg_tip_ratio")

# ---------- 5. Writer Helpers ----------
def write_cassandra(df, table_name, mode, epoch_id=None):
    if df.rdd.isEmpty(): 
        logger.info(f"Skipping Empty Batch {epoch_id} for {table_name}")
        return
    
    count = df.count()
    msg = f"Writing batch {epoch_id} to {table_name} - {count} records found" if epoch_id else f"Writing BATCH data to {table_name} - {count} records found"
    logger.info(msg)
    
    try:
        df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .options(table=table_name, keyspace=CASSANDRA_KEYSPACE) \
            .save()
        logger.info(f"Successfully wrote to {table_name}")
    except Exception as e:
        logger.error(f"FAILED writing to {table_name}: {e}")

# --- TÍCH HỢP HDFS (Batch Layer) ---
def write_hdfs(df, epoch_id):
    try:
        if df.rdd.isEmpty(): return
        logger.info(f"Writing BATCH {epoch_id} to HDFS [{HDFS_PATH}]")
        df.write.mode("append").partitionBy("event_date").parquet(HDFS_PATH)
    except Exception as e:
        logger.error(f"Failed to write to HDFS: {e}")

# ---------- 6. Main Execution Logic ----------
def main():
    spark = get_spark_session("stream")
    spark.sparkContext.setLogLevel("WARN")

    # 1. Read & Process (Common for both layers)
    raw_df = read_kafka(spark)
    final_df = process_data(raw_df, spark)

    # 2. Define Streams
    active_streams = []

    # --- A. BATCH LAYER (HDFS Dump) ---
    # Dump dữ liệu sạch xuống HDFS để sau này chạy batch job
    # Trigger 1 phút/lần để tránh tạo quá nhiều file nhỏ và giảm tải RAM
    hdfs_query = final_df.writeStream \
        .outputMode("append") \
        .foreachBatch(write_hdfs) \
        .trigger(processingTime="30 seconds") \
        .option("checkpointLocation", os.path.join(CHECKPOINT_ROOT, "hdfs_raw")) \
        .start()
    
    active_streams.append(hdfs_query)
    print("Started BATCH LAYER stream (HDFS)...")

    # --- B. SPEED LAYER (Cassandra Aggregates) ---
    configs = [
        (get_zone_agg, "30 minutes", "_30m"),
        # (get_zone_agg, "1 hour", "_1h"),
        (get_global_agg, "30 minutes", "_30m"),
        (get_peak_agg, "30 minutes", "_30m"),
        (get_payment_agg, "30 minutes", "_30m")
    ]
    
    for agg_func, interval, suffix in configs:
        agg_df = agg_func(final_df, interval)
        
        if agg_func == get_zone_agg: base = "zone_performance"
        elif agg_func == get_global_agg: base = "global_kpis"
        elif agg_func == get_peak_agg: base = "peak_analysis"
        elif agg_func == get_payment_agg: base = "payment_analysis"
        
        full_table = f"{base}{suffix}"
        ckpt = os.path.join(CHECKPOINT_ROOT, f"{base}{suffix}")

        q = agg_df.writeStream \
            .outputMode("update") \
            .foreachBatch(lambda df, id, t=full_table: write_cassandra(df, t, id)) \
            .option("checkpointLocation", ckpt) \
            .start()
        
        active_streams.append(q)
        print(f"Started SPEED LAYER stream: {full_table} [{interval}]")

    print(f"Pipeline running with {len(active_streams)} streams...")
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()