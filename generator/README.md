# Traffic Generator

This is a standalone simulation client that sends taxi trip data to the Ingestion Gateway running in Kubernetes.

## Prerequisites
*   Python 3.11+
*   The `big-data` Kubernetes cluster running with the `producer-gateway` service exposed.

## Setup (from Project root)
```bash
uv sync --frozen
```

## Running the Simulation

1.  **Port-forward the Gateway**:
    Ensure the Gateway in K8s is accessible at `localhost:8000`.
    ```bash
    kubectl -n big-data port-forward svc/producer-gateway 8000:8000
    ```

2.  **Run the Generator (from Project root)**:
    ```bash
    python generator/generator.py --gateway http://localhost:8000 --speedup 3600.0
    ```

## Options
*   `--speedup`: Simulation speed multiplier (default: 3600x).
*   `--max_records`: Stop after N records.
