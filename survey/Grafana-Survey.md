# Grafana Overview for Big Data Processing

## 1. Introduction

- Grafana is used for **data visualization and monitoring**. 
After data is collected (Kafka), processed (Spark), and stored (Cassandra / HDFS), 
Grafana creates **interactive dashboards** that help us understand real-time and historical patterns in the NYC Yellow Taxi dataset.

Our goal is to show:
- **Live analytics** — e.g., current number of trips, average fare, or passenger count per borough.
- **Batch analytics** — daily or weekly summaries from Spark Batch output.
- **Anomaly detection visuals** — such as sudden fare drops or peak-hour congestion.

---

## 2. Grafana in the Pipeline

Kafka → Spark (Streaming / Batch) → Cassandra / HDFS → Grafana

- **From Cassandra**: Read *real-time aggregated data* (e.g., trip count per minute).
- **From HDFS (optional)**: Connect to a preprocessed static dataset through a plugin or a small API layer for long-term analytics.
- **On Kubernetes**: Run as a `Deployment` service, accessible through a web UI within the cluster.

---

## 3. Connecting Grafana to Data Sources

Grafana supports multiple backends, but in our setup, **Cassandra** is the main one. Since Cassandra is not directly supported, we can either:

1. Use a **PostgREST or Prometheus-compatible bridge**, or  
2. Export selected metrics from Cassandra into a time-series database (e.g., InfluxDB) and connect Grafana to that.

For static data, CSV or Parquet exports from Spark Batch can be read through Grafana plugins or imported into another SQL/NoSQL layer (like PostgreSQL).

The main idea is: **Grafana doesn’t process data — it visualizes what’s already prepared.**

---

## 4. Key Grafana Concepts to Know

| Concept | Description |
|----------|-------------|
| **Data Source** | Where Grafana fetches data from (Cassandra, InfluxDB, PostgreSQL, etc.) |
| **Dashboard** | A collection of visual panels that share variables and filters |
| **Panel** | A single visualization (graph, table, gauge, stat) |
| **Query** | The expression Grafana sends to the data source to retrieve metrics |
| **Alert** | Rule-based notifications triggered by data thresholds (e.g., fare drop alert) |

We’ll make use of:
- **Stat and Time-Series panels** for live trends  
- **Heatmaps** for hourly traffic visualization  
- **Alerting rules** to flag data anomalies in real-time

---

## 5. Deployment Notes

Grafana will be deployed as a Kubernetes `Deployment`, exposed via a ClusterIP or NodePort service.  
It will connect to the internal Cassandra service through environment variables or a config map.

Example environment setup:
```yaml
env:
  - name: CASSANDRA_HOST
    value: cassandra-service
  - name: CASSANDRA_PORT
    value: "9042"
```

Dashboards and data source configurations can be persisted using Grafana provisioning (/etc/grafana/provisioning).

---

## 6. Next Steps

Learn Grafana basics: dashboard creation, panel types, and alert configuration.
Verify Cassandra connectivity and data format.
Build prototype dashboard with sample data (CSV or mock metrics).
Integrate with live Spark Streaming output.
Finalize UI: color scheme, legends, labeling, and interactivity.

---

## 7. Dashboard Design Plan (Subject to change)

Planning two main dashboards:

### a. Real-time Metrics Dashboard
Powered by Cassandra (streaming results).

**Panels:**
- Current number of trips in progress  
- Average fare per borough (last 5 minutes)  
- Passenger count trend (sliding window)  
- Detected anomalies (e.g., unusually low fare values)

### b. Historical Analytics Dashboard
Powered by Spark Batch output (from HDFS-curated data).

**Panels:**
- Total trips per day/week  
- Average distance and fare trends  
- Peak hour distribution (heatmap)  
- Borough-level trip density

Both dashboards will use **Grafana variables** (like date ranges or borough filters) for interactive filtering.

---
