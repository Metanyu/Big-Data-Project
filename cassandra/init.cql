CREATE KEYSPACE IF NOT EXISTS taxi_streaming
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE taxi_streaming;

-- 1. ZONE PERFORMANCE (Supports Viz 1, 2, 3, 4, 5)
-- Partitioned by Zone so you can plot multiple zones as separate series.
-- Also supports "Top Zones" by querying a specific window with ALLOW FILTERING (low cost for ~260 zones).
CREATE TABLE IF NOT EXISTS zone_performance_30m (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    pickup_zone TEXT,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_fare_per_mile DOUBLE,
    avg_speed_mph DOUBLE,
    avg_duration_sec DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS zone_performance_5m (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    pickup_zone TEXT,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_fare_per_mile DOUBLE,
    avg_speed_mph DOUBLE,
    avg_duration_sec DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS zone_performance_1h (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    pickup_zone TEXT,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_fare_per_mile DOUBLE,
    avg_speed_mph DOUBLE,
    avg_duration_sec DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS zone_performance_1d (
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    pickup_zone TEXT,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_fare_per_mile DOUBLE,
    avg_speed_mph DOUBLE,
    avg_duration_sec DOUBLE,
    PRIMARY KEY ((pickup_zone), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 2. GLOBAL KPIs (Supports Viz 6)
-- Partitioned by a static 'shard_id' to allow querying global stats by time easily.
CREATE TABLE IF NOT EXISTS global_kpis_30m (
    shard_id TEXT, 
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_speed_mph DOUBLE,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((shard_id), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS global_kpis_5m (
    shard_id TEXT, 
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_speed_mph DOUBLE,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((shard_id), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS global_kpis_1h (
    shard_id TEXT, 
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_speed_mph DOUBLE,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((shard_id), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS global_kpis_1d (
    shard_id TEXT, 
    window_start TIMESTAMP,
    window_end TIMESTAMP,
    total_trips BIGINT,
    total_revenue DOUBLE,
    avg_speed_mph DOUBLE,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((shard_id), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 3. PEAK ANALYSIS (Supports Viz 7)
-- Partitioned by Peak Category (AM Rush, PM Rush, Off-Peak).
-- Stacked Area Chart to see if Rush start(end) earlier(later) than expected.
CREATE TABLE IF NOT EXISTS peak_analysis_30m (
    window_start TIMESTAMP,
    peak_category TEXT,
    total_trips BIGINT,
    PRIMARY KEY ((peak_category), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS peak_analysis_15m (
    window_start TIMESTAMP,
    peak_category TEXT,
    total_trips BIGINT,
    PRIMARY KEY ((peak_category), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS peak_analysis_1d (
    window_start TIMESTAMP,
    peak_category TEXT,
    total_trips BIGINT,
    PRIMARY KEY ((peak_category), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

-- 4. PAYMENT ANALYSIS (Supports Viz 8)
-- Partitioned by Payment Type (Credit, Cash, etc).
CREATE TABLE IF NOT EXISTS payment_analysis_30m (
    window_start TIMESTAMP,
    payment_type TEXT,
    total_trips BIGINT,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((payment_type), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS payment_analysis_15m (
    window_start TIMESTAMP,
    payment_type TEXT,
    total_trips BIGINT,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((payment_type), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);

CREATE TABLE IF NOT EXISTS payment_analysis_1d (
    window_start TIMESTAMP,
    payment_type TEXT,
    total_trips BIGINT,
    avg_tip_ratio DOUBLE,
    PRIMARY KEY ((payment_type), window_start)
) WITH CLUSTERING ORDER BY (window_start DESC);