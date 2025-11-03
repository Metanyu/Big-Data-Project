-- Initialize Cassandra keyspace and tables for NYC Taxi Trip pipeline

-- Create keyspace
CREATE KEYSPACE IF NOT EXISTS taxi_streaming
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

-- Use keyspace
USE taxi_streaming;

-- Table for raw taxi trips (if you want to store raw data)
CREATE TABLE IF NOT EXISTS taxi_trips (
    vendor_id INT,
    trip_timestamp TIMESTAMP,
    passenger_count BIGINT,
    total_amount DOUBLE,
    PRIMARY KEY (vendor_id, trip_timestamp)
) WITH CLUSTERING ORDER BY (trip_timestamp DESC);

-- Table for windowed aggregations (5-minute windows)
-- Using a composite partition key for better query performance
CREATE TABLE IF NOT EXISTS trip_aggregations_5min (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    vendor_id INT,
    trip_count BIGINT,
    avg_passenger_count DOUBLE,
    total_revenue DOUBLE,
    avg_fare DOUBLE,
    PRIMARY KEY ((vendor_id), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- Table for hourly aggregations
CREATE TABLE IF NOT EXISTS trip_aggregations_hourly (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_passengers DOUBLE,
    PRIMARY KEY (window_start)
);
