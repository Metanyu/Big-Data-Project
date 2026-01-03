# Kubernetes

How to run this project but with Kubernetes local development environment (Kind - Kubernetes IN Docker)

---

## How to run

### 1. Deploy
This deploy script creates the cluster, builds images, and applies manifests.
```bash
./scripts/deploy.sh
```

Then in the same or a different terminal, forward the Producer's port to the localhost port:
```bash
kubectl -n big-data port-forward svc/producer-gateway 8000:8000
```

In a separate terminal, run the data generator script:
```bash
uv run python generator/generator.py
```

### 2. Access Services
Services are exposed via `NodePort` and need to be forwarded to the localhost port.

*   **Grafana**: http://localhost:3000
    ```bash
    kubectl -n big-data port-forward svc/grafana 3000:3000
    ```
*   **Kafka UI**: http://localhost:8080
    ```bash
    kubectl -n big-data port-forward svc/kafka-ui 8080:8080
    ```

### 3. Debugging with `kubectl`

`kubectl` is the command-line tool for talking to the Kubernetes API. The syntax is always:
`kubectl [command] [TYPE] [NAME] [flags]`

| Command | Description | Example |
| :--- | :--- | :--- |
| **`get`** | List resources. | `kubectl get pods -n big-data` |
| **`describe`** | Show detailed config and events (errors). | `kubectl describe pod cassandra-0 -n big-data` |
| **`logs`** | Print stdout/stderr of a container. | `kubectl logs -f deploy/spark-streaming -n big-data` |
| **`exec`** | Run a command inside a running container. | `kubectl exec -it cassandra-0 -n big-data -- cqlsh` |
| **`delete`** | Delete a resource. | `kubectl delete pod producer-xyz -n big-data` |

**Key Flags:**
*   `-n big-data`: Specifies the **Namespace**. If you forget this, `kubectl` looks in the `default` namespace and won't find your apps.
*   `-f`: Follow the logs (stream them).
*   `-w`: Watch for changes (live updates to the list).

### 4. Important Scripts:

**Reset:** Restart the pipeline with fresh data *without* destroying the cluster.
```bash
./scripts/reset.sh
```
What this does:
1.  Force Stops all pods (Instant).
2.  Wipes all data (PVCs).
3.  Restarts everything automatically.

**Stop (Freeze State):** Stop the container, keep the data.
```bash
./scripts/stop.sh
```

**Resume (Unfreeze):** Start the container, there will be a restart from all pods.
```bash
./scripts/start.sh
```

**Teardown:** Delete the cluster (Kind container).
```bash
kind delete cluster --name big-data
```

---

## 🏗 Architecture: Kind vs. Docker Compose

### Old Architecture: Docker Compose
*   **What it is**: A tool for running multi-container Docker applications on a *single host*.
*   **How it works**: It tells the Docker Daemon: "Start these 6 containers and network them together."
*   **Limitation**: It doesn't handle "node failure" (because there's only one node). Scaling is manual. Service discovery is simple DNS.

### New Architecture: Kubernetes (Kind)
*   **What it is**: **Kind** (Kubernetes IN Docker) runs a whole Kubernetes cluster *inside* Docker containers.
*   **The Difference**: Kubernetes is an **Orchestrator**. It doesn't just "run containers". It manages *State*.
    *   *Self-Healing*: If a Spark pod crashes, Kubernetes restarts it automatically.
    *   *Scheduling*: It decides *where* to run pods (simulated nodes in Kind).
    *   *Storage*: It attaches persistent disks (PVCs) to pods, regardless of where they run.

---

## 📄 Manifests Explained

Kubernetes uses YAML "Manifests" to define the *desired state*. Here is a line-by-line breakdown of our project structure:

### `00-core.yaml`: The Foundation
*   **`Namespace`**: `big-data`. This is a virtual cluster. It isolates our resources (Pods, Services, PVCs) from system components.
*   **`ConfigMap`**: Key-value pairs for configuration.
    *   `cassandra-init`: Stores the contents of `init.cql`. This allows us to inject the schema script as a file without rebuilding the image.
    *   `grafana-datasources`: Stores the `datasource.yaml` so Grafana knows how to talk to Cassandra on boot.

### `01-data-layer.yaml`: The State (Kafka & Cassandra)
This file defines **StatefulSets** and **Services**.

*   **`StatefulSet` vs `Deployment`**:
    *   We use `StatefulSet` because Kafka and Cassandra need **Stable Network Identities** (`cassandra-0`) and **Stable Storage**. If `cassandra-0` dies, it must come back with the same name and the same data volume.
*   **Field Breakdown**:
    *   `serviceName`: Links the Pods to the Headless Service for DNS discovery.
    *   `volumeClaimTemplates`: Automatically creates a PersistentVolumeClaim (PVC) for *each* replica. This creates the "virtual hard drive" (`kafka-data`).
    *   `readinessProbe`: Use `cqlsh` to ask "Are you ready?". If this fails (non-zero exit), Kubernetes won't send traffic to the pod.

### `02-init-job.yaml`: Schema Initialization
*   **`Job`**: A Pod that runs *once* to completion.
*   **How it works**:
    *   It mounts the `cassandra-init` ConfigMap as a file at `/cassandra/init.cql`.
    *   It runs `cqlsh` to execute that script.
    *   `restartPolicy: OnFailure`: If the script fails (e.g., connection refused), K8s retries until it works.

### `03-apps.yaml`: The Logic (Spark & Producer)
This file defines **Deployments** and **PersistentVolumeClaims**.

*   **`Deployment`**: Used for stateless apps.
    *   `imagePullPolicy: Never`: **Crucial for local dev**. It tells K8s "Use the image I built locally, don't try to download from the internet."
*   **`PersistentVolumeClaim` (PVC)**:
    *   `spark-checkpoints-pvc`: A request for 1Gi of storage. Spark needs this to save its offset positions. If the pod crashes, it reads this PVC to resume processing exactly where it left off (Fault Tolerance).

### `04-ui.yaml`: The Visuals (Grafana & Kafka UI)
*   **`NodePort` Service**:
    *   `type: NodePort`: Opens a specific port on the "Node" (the Kind container).
    *   `nodePort: 30300`: We manually pinned this port so we know where to access it. (Though port-forwarding is superior for local dev).

---

## 🏭 Industry Standards & Production Tuning

We configured this cluster for *Local Development*, but here is how it compares to *Production Standards*:

### 1. Replicas & Availability
*   **Our Setup**: `replicas: 1`. Single point of failure, but efficient for local dev.
*   **Standard**: `replicas: 3` (minimum).
    *   Kafka: 3 Brokers to allow voting/quorum.
    *   Cassandra: 3 Nodes (Ring architecture).
    *   Spark: Multiple Executor pods scaling horizontally based on load (HPA).

### 2. Data Persistence
*   **Our Setup**: `standard` StorageClass (HostPath in Kind).
*   **Standard**: Cloud Storage (AWS EBS, Google Persistent Disk).
    *   For **Kafka/Cassandra**: Use fast SSD-backed PVCs (`io1` or `gp3` on AWS).
    *   For **Spark Checkpoints**: Use Object Storage (S3/GCS) instead of block storage, as checkpoints are write-heavy and don't require block-level performance.

### 3. Resource Limits
*   **Our Setup**: No limits defined (uses whatever your laptop handles).
*   **Standard**: Explicit `resources.requests` and `limits`.
    ```yaml
    resources:
      requests:
        memory: "4Gi"  # Guaranteed RAM
        cpu: "2"       # Guaranteed CPU cores
    ```
    This prevents a rogue query from crashing the entire node.
