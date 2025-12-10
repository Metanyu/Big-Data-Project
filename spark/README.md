## NYC Taxi Data Streaming (and occasionally Batch Processing) Pipeline

### How do I run?

```bash
# Perpetually streaming
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.1,com.datastax.spark:spark-cassandra-connector_2.13:3.5.1 spark/streaming.py stream

# Periodic batch job (dont't run these 2 in the same terminal)
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.1,com.datastax.spark:spark-cassandra-connector_2.13:3.5.1 spark/streaming.py batch

```

### Why many files here?

`streaming.py` is the only one you should care about. `streaming_old.py` is the original script for the now deprecated Cassandra schema, kept for config reference point.

### What does that script do?

Transformations and aggregations adhering to these visualization requirements:

> [!tip]
>
> Viz 1-5 **Zone Performance:** time series with short aggregation (5m, 1h, 1d), mostly grouped by zone.
>
> Viz 6 **Global KPIs:** stat cards with short aggregation (5m, 1h, 1d).
>
> Viz 7 **Peak Analysis:** stacked area or bar to observe rush sccumulation/transition, longer agg (15m, 1d).
>
> Viz 8 **Payment Analysis:** payment type trend (or to detect anomaly i.e. payment gateway down), longer agg (15m, 1d).

1. ?

Type: Time-series line chart with multiple series

Metrics:
Total revenue per time window (hourly)
Grouped by top 5-7 zones

2. Trip Demand by Zone (Line Chart)

Type: Multi-line time-series chart

Metrics:
Trip count per time window
One line per major zone (airports, business districts, tourist areas)

3. Top Zones by Total Revenue (Bar Chart)

Type: Horizontal bar chart (sorted descending)

Metrics:
Total accumulated revenue per zone
Top 10 zones

4. Average Fare Per Mile by Zone (Line Chart)

Type: Time-series line chart

Metrics:
Fare amount / trip distance ratio
Tracked over time for top 3-5 zones

5. Operational Efficiency: Average Speed (Line Chart)

Type: Time-series line chart

Metrics:
Average speed (mph) per time window
By zone

6. Real-Time KPIs (Stat Panels)

Type: Single-value stat cards

Metrics:
Total trips (count)
Total revenue (currency)
Average speed (mph)
Average tip rate (percentage)

7. Peak vs Off-Peak Distribution (Stacked Area/Bar)

Type: Stacked area chart or grouped bar chart

Metrics:
Trip count by peak category (AM Rush, PM Rush, Off-Peak)
Over time or by zone

8. Payment Type Distribution (Pie/Donut Chart)

Type: Pie or donut chart

Metrics:
Trip count by payment type (credit, cash, etc.)
Average tip ratio per payment type
