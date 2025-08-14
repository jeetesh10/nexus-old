# Nexus Platform: Kubernetes Manual Setup

This document outlines the manual, declarative setup for the Nexus Platform's core services on Kubernetes.

## Directory Structure & Pre-requisites

1.  The project's root folder must be named `nexus`.
2.  All commands, including the deployment script, should be run from the parent directory (`workspace`).
3.  Ensure `kubectl` is configured for your cluster.

## How to Deploy and Verify

1.  **From the `workspace` directory, run the main deployment script:**
    ```bash
    ./nexus/scripts/deploy/deploy-all-services.sh
    ```
    This single script deploys all platform components. It will evolve as new services are added.

2.  **Interactive Steps:**
    - The script will prompt you to watch the pod status.
    - It will also ask if you want to set up port-forwarding for the monitoring services, making them available on your localhost.
    - **To stop the port-forwards later, run this command:** `pkill -f "kubectl port-forward"`

## Known Issues (As of August 14, 2025)

- **Loki Log Ingestion:** While all services are running, logs collected by Promtail are not yet appearing in Grafana. The issue is confirmed to be with Promtail's configuration for discovering log file paths within the Kind cluster environment.

