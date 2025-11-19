-- Create Keyspace
CREATE KEYSPACE IF NOT EXISTS taxi_streaming 
WITH REPLICATION = { 
   'class' : 'SimpleStrategy', 
   'replication_factor' : 1 
};

USE taxi_streaming;

-- 1. Demand & Revenue Table
-- Query: Group by window (hour), zone, peak_category
CREATE TABLE IF NOT EXISTS demand_dynamics (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    pickup_zone INT,
    peak_category TEXT,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_distance DOUBLE,
    avg_fare_per_mile DOUBLE,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start, peak_category)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 2. Operational Efficiency Table
-- Query: Group by window (30 min), zone
CREATE TABLE IF NOT EXISTS operational_efficiency (
    window_start TIMESTAMP,
    pickup_zone INT,
    avg_speed DOUBLE,
    avg_duration_sec DOUBLE,
    avg_occupancy DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 3. Rider Behavior Table
-- Query: Group by window (hour), payment_type, distance_bucket
CREATE TABLE IF NOT EXISTS rider_behavior (
    window_start TIMESTAMP,
    payment_type BIGINT,
    distance_bucket TEXT,
    total_trips BIGINT,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((payment_type), window_start, distance_bucket)
) WITH CLUSTERING ORDER BY (window_start DESC);