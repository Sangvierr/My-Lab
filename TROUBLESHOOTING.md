# 🏛️ Hybrid AI Home-Lab (Airflow 3.0 & Kubernetes)

This project implements a **Hybrid MLOps Infrastructure** connecting a **Control Plane (MacBook)** and a **Worker Node (Windows Desktop with GPU)**.

It is designed to study and develop data pipelines involving:
* **Orchestrator:** Apache Airflow 3.0.2 (running on Kubernetes)
* **AI Engine:** Ollama (Llama3, DeepSeek-R1, Qwen2.5)
* **Database:** Oracle 11g (Legacy System) & PostgreSQL (Airflow Metadata)
* **Infrastructure:** Kubernetes (Docker Desktop) on WSL2

---

## 🏗 Architecture

- **Client (Control Plane):** M2 MacBook Air
    - Role: Code development, Cluster management (`kubectl`), Helm deployment.
- **Server (Worker Node):** Windows Desktop (RTX 5070, AMD 7800X3D)
    - Role: Hosting Kubernetes Cluster, GPU-accelerated LLM inference.

```mermaid
graph LR
    Mac[💻 MacBook M2] -- "kubectl / Helm" --> WinIP[📡 Windows IP]
    WinIP -- "Port Proxy (netsh)" --> K8s[☸️ Kubernetes]
    K8s --> Airflow[🚀 Airflow 3.0 Pods]
    Airflow -- "Rest API" --> Ollama[🦙 Ollama (Host GPU)]
    Airflow -- "JDBC" --> Oracle[🗄️ Oracle 11g (Host)]
```

## 🛠️ Prerequisites & Setup
### 1. Windows (Server Side)
Since Docker Desktop on Windows binds ports to 127.0.0.1 by default, you must configure a Port Proxy to allow the MacBook to connect.

Run the following in PowerShell (Admin):

```PowerShell
# 1. Open Firewall ports
New-NetFirewallRule -DisplayName "K8s-Allow-6443" -Direction Inbound -LocalPort 6443 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Ollama-Allow-11434" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow

# 2. Set up Port Forwarding (Replace [YOUR_WIN_IP] with actual IP)
# For Kubernetes API
netsh interface portproxy add v4tov4 listenaddress=[YOUR_WIN_IP] listenport=6443 connectaddress=127.0.0.1 connectport=6443
# For Ollama API
netsh interface portproxy add v4tov4 listenaddress=[YOUR_WIN_IP] listenport=11434 connectaddress=127.0.0.1 connectport=11434
```

### 2. MacBook (Client Side)
- Install Tools: brew install kubectl helm

- Configure Kubeconfig: Edit ~/.kube/config:
    - Set server: https://[WIN_IP]:6443
    - Add insecure-skip-tls-verify: true (to bypass SSL errors)

## 🚀 Installation (Airflow 3.0)
We use the official Helm Chart with specific overrides for Windows/Airflow 3.0 compatibility.

### 1. Deploy via Helm

```Bash
helm upgrade --install airflow apache-airflow/airflow \
  --namespace airflow \
  --create-namespace \
  --set postgresql.image.tag=16 \
  --set webserver.enabled=true
```
- postgresql.image.tag=16: Fixes ImagePullBackOff issue caused by deprecated Bitnami tags.
- webserver.enabled=true: Ensures UI components are deployed.

### 2. Access the Airflow UI
In Airflow 3.0, the UI is served via the API Server.

```Bash
kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow
URL: http://localhost:8080
```

## 🔧 Troubleshooting (Log)

### Issue 1: PostgreSQL ImagePullBackOff
- Symptom: The DB pod fails to pull the image bitnami/postgresql:16.1.0-debian-11-r15.

- Cause: The specific image tag referenced by the Helm chart is missing or deprecated.

- Solution: Manually pull the latest version on Windows and re-tag it.

    ```PowerShell
    # On Windows PowerShell
    docker pull bitnami/postgresql:latest
    docker tag bitnami/postgresql:latest bitnami/postgresql:16
    ```

### Issue 2: Scheduler Init:CrashLoopBackOff
- Symptom: Scheduler/Triggerer pods get stuck in Init state.

- Cause: The database migration job (airflow-run-airflow-migrations) failed or stalled, leaving the DB schema empty.

- Solution: Delete the stuck job and force a Helm upgrade.

    ```Bash
    # On Mac Terminal
    kubectl delete job airflow-run-airflow-migrations -n airflow
    helm upgrade --install airflow ... (run the install command again)
    ```

### Issue 3: Webserver Service Not Found
- Symptom: kubectl port-forward svc/airflow-webserver fails.

- Cause: Airflow 3.0 architecture changes; UI is accessed via the API Server.

- Solution: Port-forward to svc/airflow-api-server instead.