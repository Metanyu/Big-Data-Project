-- Initialize Cassandra keyspace and tables for NYC Taxi Trip pipeline

CREATE KEYSPACE IF NOT EXISTS taxi_streaming
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE taxi_streaming;

-- Table for hourly aggregations (NEEDED FOR PANELS 1 & 2)
CREATE TABLE IF NOT EXISTS trip_aggregations_hourly (
    partition_key TEXT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_passengers DOUBLE,
    PRIMARY KEY ((partition_key), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 1. Demand & Revenue Table (UPDATED for panel queries)
CREATE TABLE IF NOT EXISTS demand_dynamics (
    pickup_zone TEXT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    peak_category TEXT,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_distance DOUBLE,
    avg_fare_per_mile DOUBLE,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start, peak_category)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 2. Operational Efficiency Table
CREATE TABLE IF NOT EXISTS operational_efficiency (
    pickup_zone TEXT,
    window_start TIMESTAMP,
    avg_speed DOUBLE,
    avg_duration_sec DOUBLE,
    avg_occupancy DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 3. Rider Behavior Table
CREATE TABLE IF NOT EXISTS rider_behavior (
    payment_type BIGINT,
    window_start TIMESTAMP,
    distance_category TEXT,
    total_trips BIGINT,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((payment_type), window_start, distance_category)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- Table for 5-minute aggregations (for vendor_id variable)
CREATE TABLE IF NOT EXISTS trip_aggregations_5min (
    vendor_id INT,
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    trip_count BIGINT,
    avg_passenger_count DOUBLE,
    total_revenue DOUBLE,
    avg_fare DOUBLE,
    PRIMARY KEY ((vendor_id), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- TIME-SERIES OPTIMIZED TABLES FOR GRAFANA DASHBOARDS
-- These tables have time-based partition keys for efficient time-series queries

-- Time-series view of demand_dynamics for line charts
CREATE TABLE IF NOT EXISTS demand_timeseries (
    time_bucket TEXT,
    window_start TIMESTAMP,
    pickup_zone TEXT,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_fare_per_mile DOUBLE,
    PRIMARY KEY ((time_bucket), window_start, pickup_zone)
) WITH CLUSTERING ORDER BY (window_start DESC, pickup_zone ASC);

-- Time-series view of operational_efficiency for line charts
CREATE TABLE IF NOT EXISTS ops_timeseries (
    time_bucket TEXT,
    window_start TIMESTAMP,
    pickup_zone TEXT,
    avg_speed DOUBLE,
    avg_duration_sec DOUBLE,
    avg_occupancy DOUBLE,
    PRIMARY KEY ((time_bucket), window_start, pickup_zone)
) WITH CLUSTERING ORDER BY (window_start DESC, pickup_zone ASC);

-- Zone-aggregated revenue for bar charts (total across all time)
CREATE TABLE IF NOT EXISTS zone_revenue_totals (
    zone_group TEXT,
    pickup_zone TEXT,
    total_revenue DOUBLE,
    total_trips BIGINT,
    PRIMARY KEY ((zone_group), total_revenue, pickup_zone)
) WITH CLUSTERING ORDER BY (total_revenue DESC, pickup_zone ASC);