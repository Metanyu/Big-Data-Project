# Big Data Processing Capstone Project — Meeting Notes
Last Updated: 4/10/25

[![N|Solid](https://cldup.com/dTxpPi9lDf.thumb.png)](https://nodesource.com/products/nsolid)

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

## Overview 
Discuss Architecture options:
- Lambda Architecture: Batch + Stream processing
- Kappa Architecture: Stream-only processing 

Discuss tools use.
Dataset: NYC TLC Yellow Taxi Trip Records
Deployment: All components deployed on Kubernetes

## System Design Summary

*Streaming Data:* Source -> Kafka -> Spark Streaming for processing -> NoSQL DB -> Live Dashboard
- Handle late data via *watermarking*
- Perform real-time aggregations (e.g., avg fare, trip count per zone)
- Write results to NoSQL (Cassandra)
- Output: Live dashboard (Grafana)

*Batch Data:* Source -> Kafka -> HDFS -> Spark Batch -> Static Analysis for Dashboard 
- Source data stored in HDFS (historical data / raw zone)
- Spark Batch jobs perform scheduled aggregations
- Optimizations: partitioning, bucketing, caching
- Output: static analytics → dashboard (batch layer visualization)

If *Kappa* architecture, historical data will be treated as stream and is to be replay from Kafka if needed.

## Components Overview
| Layer | Technology | Purpose |
|-------|------------|---------|
| Message Queue | Apache Kafka | Simulate and ingest trip events
| Batch Processing | Spark Batch (PySpark) | Periodic data aggregation from HDFS
| Streaming Processing | Spark Structured Streaming | Real-time analytics from Kafka
| Distributed Storage | HDFS | Store raw and curated historical data
| Database | Cassandra (NoSQL) | Store aggregated results for live querying
| Visualization | Grafana | Live + static dashboards
| Deployment | Kubernetes | Container orchestration for all services

## Data Pipeline Summary

| Stage             | Input                       | Processing                                   | Output                               |
| ----------------- | --------------------------- | -------------------------------------------- | ------------------------------------ |
| **Ingestion**     | TLC Yellow Taxi CSV/Parquet | Kafka producer simulates streaming           | Kafka topic `taxi_trips`             |
| **Batch Layer**   | HDFS (raw zone)             | Spark Batch (aggregations, caching, joins)   | HDFS curated data → static dashboard |
| **Stream Layer**  | Kafka topic                 | Spark Streaming (watermark, UDF, window ops) | Cassandra → Grafana                  |
| **Visualization** | Cassandra/HDFS              | Grafana dashboard                            | Real-time + static analytics         |
## Team Roles & Responsibilities

| Member  | Role                   | Responsibilities                                       |
| ------- | ---------------------- | ------------------------------------------------------ |
| **Mễ**  | Kafka Engineer         | Set up Kafka cluster and producer simulation           |
| **Bảo** | Spark Engineer         | Develop Spark Streaming + Batch pipelines              |
| **An**  | Spark Engineer         | Batch analytics + optimization (partitioning, caching) |
| **Nam** | Database Engineer      | Design Cassandra schema, integrate Spark sink          |
| **Đức** | Visualization Engineer | Build Grafana dashboard (live + static views)          |

##  Key Tasks & Notes
**Kafka**
- Learn Kafka fundamentals
- Simulate data stream from TLC Yellow Taxi dataset
- Maintain topics and partitions

**Spark**
- Build **Streaming pipeline** (from Kafka → Cassandra)
- Build **Batch pipeline** (from HDFS → visualization)

**HDFS**
- Store historical trip records under `/hdfs/raw/`
- Partition by date for optimized access

**Cassandra**
- Define schema for real-time aggregated metrics

**Visualization**
- Integrate Grafana with Cassandra data source
- Create two panels:
-- Live metrics (stream layer)
-- Periodic analytics (batch layer)
- Add anomaly detection visual (e.g., sudden fare drop alert)

## Deployment

| Component               | Deployment Mode | Tool       |
| ----------------------- | --------------- | ---------- |
| Kafka + Zookeeper       | StatefulSet     | Kubernetes |
| Spark Batch + Streaming | Spark-on-K8s    | Kubernetes |
| Cassandra               | StatefulSet     | Kubernetes |
| Grafana                 | Deployment      | Kubernetes |
| HDFS (optional)         | StatefulSet     | Kubernetes |

---