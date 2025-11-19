## NYC Taxi Data Streaming Pipeline

Sẽ còn phải sửa nhiều phụ thuộc viz 😔 Equivalent `init.cql` for Cassandra I put in this very same directory.

Nguồn dựng feature: [Mễ's nooootion](https://www.notion.so/Erm-Features-and-stuff-2aa06a8a8ce2807eb4bdcf764aa39399)

### Architecture

- Source: Kafka Topic (taxi-trips)
- Processing: Apache Spark (Structured Streaming)
- Sink: Cassandra Keyspace (taxi_streaming)

### Data Pipeline Details

1. Data Cleaning & Rules

- Trips with positve mileage, cap at 1000 miles.
- Passenger count must be between 1 and 9.
- Trip Duration must be between 1 minute and 4 hours.
- Fares must be non-negative.
- Unknown Zones: PULocationID must be valid (< 264).

2. Feature Engineering

- `pickup_zone`: Resolves ID to human-readable zone name (e.g., "JFK Airport") via Broadcast Join.
- `speed_mph`: Calculated average speed based on distance/duration.
- `peak_category`:
    - `AM Rush`: 7 AM - 10 AM (Weekdays)
    - `PM Rush`: 4 PM - 8 PM (Weekdays)
    - `Off-Peak`: All other times
- `distance_category`:
    - `Short (<2m)`
    - `Medium (2-10m)`
    - `Long (>10m)`

3. Aggregation Tables (Cassandra)

**Table 1:** demand_dynamics

**Goal:** Analyze high-level demand and revenue trends per zone.

- Granularity: Hourly Windows
- Key: (pickup_zone, peak_category)
- Fields:
    - window_start, window_end: Time range.
    - total_trips: Volume of rides.
    - total_revenue: Sum of fares + surcharges + tips.
    - avg_fare_per_mile: Efficiency metric.
    - avg_tip_ratio: Tip / Total amount.

**Table 2:** operational_efficiency

**Goal:** Monitor traffic conditions and fleet efficiency.

- Granularity: 30-minute Windows
- Key: pickup_zone
- Fields:
    - avg_speed: Average MPH in that zone (detects traffic jams).
    - avg_duration_sec: How long trips take starting from this zone.
    - avg_occupancy: Passenger efficiency.

**Table 3:** rider_behavior

**Goal:** Understand how payment methods and trip lengths correlate.

- Granularity: Hourly Windows
- Key: (payment_type, distance_category)
- Fields:
    - total_trips: Count of rides.
    - avg_tip_ratio: Do people tip better on long rides or credit card payments?