Perfect — since your team already has roles and a clear system design, we can now turn that into a **practical, week-by-week roadmap** designed for both learning and parallel development.

This plan assumes you’re starting from your **local Kafka prototype** and aiming for a **Kappa architecture deployment on Kubernetes with Strimzi (KRaft) + Schema Registry + Spark + Cassandra + Grafana**.

---

# 🗓️ Detailed Project Roadmap (8–9 Weeks)

> 🎯 Goal: Deploy a fully working end-to-end real-time pipeline (Kappa architecture)
> 🧩 Team size: 5 members (Kafka, Spark x2, Cassandra, Grafana)
> 💡 Tech stack: Kafka (KRaft) + Schema Registry + Spark Streaming + Cassandra + Grafana on Kubernetes

---

## **📅 Week 1 – Foundations & Environment Setup**

**Objective:** Everyone gets a working local environment and basic Kubernetes familiarity.

| Member               | Tasks                                                                                                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **All Members**      | - Install Docker Desktop + Minikube or kind (local Kubernetes cluster) <br>- Learn basic `kubectl` commands (pods, deployments, services) <br>- Learn YAML structure for K8s manifests |
| **Mễ (Kafka)**       | - Read Strimzi Operator docs (focus on KRaft mode) <br>- Practice deploying a Kafka cluster locally via Strimzi YAML                                                                   |
| **Bảo & An (Spark)** | - Set up local Spark Structured Streaming (read/write Kafka) <br>- Review Avro and Schema Registry integration in Spark                                                                |
| **Nam (Cassandra)**  | - Learn about Cassandra Docker image, replication, and CQL basics                                                                                                                      |
| **Đức (Grafana)**    | - Install Grafana locally and connect to any test data source (CSV or SQLite)                                                                                                          |

**Deliverables:**

* Everyone can deploy pods on local Kubernetes.
* Kafka runs on Strimzi (in KRaft mode) on one machine.

---

## **📅 Week 2 – Kafka & Schema Registry Setup**

**Objective:** Get Kafka cluster and Schema Registry running on Kubernetes.

| Member              | Tasks                                                                                                                                                 |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Mễ (Kafka)**      | - Deploy Kafka + Schema Registry on K8s <br>- Test producing/consuming Avro messages from local Python client <br>- Register `taxi-trips` Avro schema |
| **Bảo (Spark)**     | - Write small Spark Structured Streaming job that reads Avro data from Schema Registry locally                                                        |
| **Nam (Cassandra)** | - Deploy Cassandra on K8s (StatefulSet + Service)                                                                                                     |
| **An (Support)**    | - Create Dockerfile for the producer microservice (reads dataset, sends Avro messages)                                                                |
| **Đức (Grafana)**   | - Deploy Grafana to K8s via Helm and expose via NodePort                                                                                              |

**Deliverables:**

* Kafka + Schema Registry pods running and reachable inside cluster.
* Topic `taxi-trips` created and schema registered.
* Dockerized producer ready to push Avro messages.

---

## **📅 Week 3 – Kafka Producer Integration**

**Objective:** Stream TLC Taxi data into Kafka using Avro format.

| Member  | Tasks                                                                                                        |
| ------- | ------------------------------------------------------------------------------------------------------------ |
| **Mễ**  | - Create Kubernetes Deployment for producer (Python + Avro) <br>- Verify schema compatibility using REST API |
| **An**  | - Automate producer build via `Dockerfile` and test on Minikube                                              |
| **Bảo** | - Test Spark job to consume the `taxi-trips` topic from within the same K8s cluster                          |
| **Nam** | - Prepare basic Cassandra schema (trip_metrics table)                                                        |
| **Đức** | - Design mock dashboard layout in Grafana (trip count, avg fare, etc.)                                       |

**Deliverables:**

* Producer container deployed, sending Avro messages to Kafka.
* Schema Registry integration verified.
* Spark can read raw messages.

---

## **📅 Week 4 – Spark Streaming Pipeline (Core Stage)**

**Objective:** Build and deploy Spark Structured Streaming job.

| Member  | Tasks                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------- |
| **Bảo** | - Implement main Spark pipeline: read from Kafka → process (windowing, watermark, aggregation) → write to Cassandra |
| **An**  | - Add UDFs and real-time metric logic (avg fare per zone, total trips, etc.)                                        |
| **Mễ**  | - Support Spark connection with Kafka inside cluster (network setup, bootstrap servers)                             |
| **Nam** | - Finalize Cassandra schema and test inserts                                                                        |
| **Đức** | - Begin integrating Grafana with Cassandra (using plugin or direct query)                                           |

**Deliverables:**

* Spark job deployed as a Kubernetes job/pod.
* Live stream of processed metrics in Cassandra.

---

## **📅 Week 5 – Cassandra Integration & Data Validation**

**Objective:** Ensure Spark writes to Cassandra correctly and data is consistent.

| Member       | Tasks                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------- |
| **Bảo & An** | - Debug Cassandra writes, fix schema mismatches <br>- Add error handling + checkpointing in Spark |
| **Nam**      | - Tune Cassandra performance (replication factor, compaction)                                     |
| **Mễ**       | - Set up Kafka retention and partitions for throughput                                            |
| **Đức**      | - Build live panels in Grafana that show Cassandra data in real time                              |

**Deliverables:**

* Valid, continuous data flow Kafka → Spark → Cassandra.
* Live metrics visible in Grafana.

---

## **📅 Week 6 – Monitoring, Scaling, and Optimization**

**Objective:** Add resilience and scalability.

| Member       | Tasks                                                                                  |
| ------------ | -------------------------------------------------------------------------------------- |
| **Mễ**       | - Add Prometheus metrics for Kafka and Schema Registry                                 |
| **Bảo & An** | - Enable Spark structured streaming checkpoint directory (for exactly-once guarantees) |
| **Nam**      | - Add backup/restore strategy for Cassandra (persistent volumes)                       |
| **Đức**      | - Visualize Kafka and Spark metrics in Grafana (system dashboards)                     |

**Deliverables:**

* Observable system with monitoring.
* StatefulSets have persistent volumes configured.

---

## **📅 Week 7 – CI/CD and Team Collaboration**

**Objective:** Automate build and deployment for all services.

| Member           | Tasks                                                                |
| ---------------- | -------------------------------------------------------------------- |
| **An (Support)** | - Write GitHub Actions or Jenkinsfile for image build and deployment |
| **Mễ & Nam**     | - Write Helm charts or Kustomize templates for all components        |
| **All**          | - Document deployment steps clearly for new team members             |

**Deliverables:**

* One-command deployment (`kubectl apply -k ./k8s` or `helm install`).
* Working CI/CD pipeline.

---

## **📅 Week 8 – Final Integration & Demo**

**Objective:** Demo-ready end-to-end system.

| Member          | Tasks                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------- |
| **All Members** | - Integrate all components in a single K8s namespace <br>- Run live demo with TLC data streaming into Grafana dashboard |
| **Đức**         | - Polish dashboard and add alert rules                                                                                  |
| **Mễ**          | - Perform load test with higher Kafka throughput                                                                        |
| **Bảo & An**    | - Record metrics for data latency and watermark correctness                                                             |
| **Nam**         | - Final consistency check for Cassandra tables                                                                          |

**Deliverables:**

* Fully automated Kappa pipeline on K8s.
* Live dashboard demo showing streaming analytics.

---

## 📘 Optional Week 9 (Stretch)

* Add **Kafka Connect + S3 Sink** (to persist raw events)
* Add **Data replay pipeline** (for reprocessing)
* Add **Alerting via Grafana** (e.g., fare anomaly detection)

---

## 🧭 Next Steps You Can Start *Now*

1. Initialize a shared **GitHub repo**:

   ```
   /kafka/
   /spark/
   /cassandra/
   /grafana/
   /k8s/
   /docs/
   ```
2. Add a `README.md` that tracks weekly progress.
3. Assign everyone their Week 1–2 learning tasks (I can list good materials for each person if you want next).

---

Would you like me to make a **Week 1–2 learning plan with links and tutorials** tailored for each member (Kafka, Spark, Cassandra, Grafana, Deployment)?
That would help everyone ramp up smoothly in parallel.
