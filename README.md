# Visitor Counter - Cloud & Hybrid Kubernetes Project

An enterprise-ready, containerized Visitor Counter Web Application (Flask + Redis) deployed across Kubernetes clusters, demonstrating auto-scaling (HPA), hybrid cloud failover, and measured cost optimization techniques.

---

## Project Structure

```
CLOUD PROJECT/
├── app/
│   ├── app.py                      # Flask application (visitor counter, healthz, ready, cpu-stress)
│   ├── requirements.txt            # Python dependencies (Flask, Redis, Gunicorn)
│   ├── Dockerfile                  # Multi-stage optimized production Dockerfile (~225MB)
│   ├── Dockerfile.baseline         # Single-stage unoptimized baseline Dockerfile (~1.64GB)
│   └── templates/
│       └── index.html              # Modern dashboard UI
├── docker-compose.yml              # Local container execution (Task 1)
├── k8s/
│   ├── base/
│   │   ├── redis-deployment.yaml   # Redis cache deployment with resource limits & probes
│   │   ├── redis-service.yaml      # Redis ClusterIP service
│   │   ├── web-deployment.yaml     # 2-replica Flask web deployment
│   │   ├── web-service.yaml        # Web NodePort service
│   │   └── hpa.yaml                # Horizontal Pod Autoscaler (min 2, max 6, 50% CPU)
│   ├── private/
│   │   └── web-deployment.yaml     # Private Cluster overlay (On-Premises)
│   ├── public/
│   │   └── web-deployment.yaml     # Public Cloud overlay (AWS/GCP Simulation)
│   ├── kind-private.yaml           # Kind cluster config (hostPort 30081 -> containerPort 30080)
│   └── kind-public.yaml            # Kind cluster config (hostPort 30082 -> containerPort 30080)
├── hybrid/
│   ├── failover_proxy.py           # Hybrid Load Balancer & Automatic Failover Proxy (Port 8080)
│   └── nginx-failover.conf         # Nginx upstream backup failover configuration
├── scripts/
│   ├── load_test.py                # Concurrent load generator & HPA scaler monitor
│   ├── test_failover.py            # High availability failover verification script
│   └── cost_analysis.py            # Financial and cost modeling comparison engine
└── docs/
    └── COST_OPTIMIZATION_REPORT.md # In-depth cost optimization report with measured values
```

---

## Quick Start & Verification

### 1. Local Container Execution (Docker Compose)
```bash
docker compose up -d
curl http://localhost:5001/
curl http://localhost:5001/ready
```

### 2. Kubernetes Deployment & Self-Healing
```bash
# Check running pods in the private cluster
kubectl --context kind-private-cluster get pods -o wide

# Test self-healing: delete a pod and watch Kubernetes recreate it
kubectl --context kind-private-cluster delete pod <pod-name>
kubectl --context kind-private-cluster get pods
```

### 3. Horizontal Pod Autoscaler (HPA) Load Test
```bash
# Run the load test to trigger CPU load and monitor replica count
python3 scripts/load_test.py http://localhost:30081/cpu-stress?duration=0.5 10 45 kind-private-cluster
```

### 4. Hybrid Cloud Failover Demonstration
```bash
# Start the failover proxy
python3 hybrid/failover_proxy.py &

# Query traffic (routes to Private Cluster by default)
curl http://localhost:8080/?format=json

# Simulate disaster: stop private cluster
docker stop private-cluster-control-plane

# Query traffic (routes automatically to Public Cloud with zero downtime)
curl http://localhost:8080/?format=json

# Recover private cluster
docker start private-cluster-control-plane
```

### 5. Cost Optimization Analysis
```bash
python3 scripts/cost_analysis.py
```
