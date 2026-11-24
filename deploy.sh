#!/usr/bin/env bash
set -e

# Add common binary paths
export PATH="/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin:$PATH"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "=================================================================="
echo "      VISITOR COUNTER - CLOUD & HYBRID DEPLOYMENT AUTOMATOR       "
echo "=================================================================="

ACTION="${1:-all}"

case "$ACTION" in
    compose)
        echo -e "\n[+] Deploying locally with Docker Compose..."
        docker compose up --build -d
        echo -e "\n[✓] Deployed! Visit: http://localhost:5001"
        ;;

    k8s)
        echo -e "\n[1/5] Building Docker Image..."
        docker build -t visitor-counter:v1 ./app

        echo -e "\n[2/5] Creating Hybrid Clusters (Private & Public)..."
        kind get clusters | grep -q "private-cluster" || kind create cluster --config k8s/kind-private.yaml
        kind get clusters | grep -q "public-cluster" || kind create cluster --config k8s/kind-public.yaml

        echo -e "\n[3/5] Loading Container Images into Clusters..."
        docker save visitor-counter:v1 -o /tmp/vc.tar
        docker cp /tmp/vc.tar private-cluster-control-plane:/vc.tar
        docker exec private-cluster-control-plane ctr -n k8s.io images import /vc.tar
        docker cp /tmp/vc.tar public-cluster-control-plane:/vc.tar
        docker exec public-cluster-control-plane ctr -n k8s.io images import /vc.tar

        docker save redis:7-alpine -o /tmp/rd.tar
        docker cp /tmp/rd.tar private-cluster-control-plane:/rd.tar
        docker exec private-cluster-control-plane ctr -n k8s.io images import /rd.tar
        docker cp /tmp/rd.tar public-cluster-control-plane:/rd.tar
        docker exec public-cluster-control-plane ctr -n k8s.io images import /rd.tar

        echo -e "\n[4/5] Deploying Workloads to Kubernetes..."
        # Private Cluster
        kubectl --context kind-private-cluster apply -f k8s/base/redis-deployment.yaml
        kubectl --context kind-private-cluster apply -f k8s/base/redis-service.yaml
        kubectl --context kind-private-cluster apply -f k8s/private/web-deployment.yaml
        kubectl --context kind-private-cluster apply -f k8s/base/web-service.yaml

        # Metrics Server & HPA on Private Cluster
        kubectl --context kind-private-cluster apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml || true
        kubectl --context kind-private-cluster patch deployment metrics-server -n kube-system --type='json' -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]' || true
        kubectl --context kind-private-cluster apply -f k8s/base/hpa.yaml

        # Public Cluster
        kubectl --context kind-public-cluster apply -f k8s/base/redis-deployment.yaml
        kubectl --context kind-public-cluster apply -f k8s/base/redis-service.yaml
        kubectl --context kind-public-cluster apply -f k8s/public/web-deployment.yaml
        kubectl --context kind-public-cluster apply -f k8s/base/web-service.yaml

        echo -e "\n[5/5] Checking Pod Status..."
        sleep 5
        echo -e "\n--- Private Cluster Pods ---"
        kubectl --context kind-private-cluster get pods
        echo -e "\n--- Public Cluster Pods ---"
        kubectl --context kind-public-cluster get pods

        echo -e "\n[✓] Kubernetes Deployment Completed!"
        echo "  - Private Cluster URL: http://localhost:30081"
        echo "  - Public Cluster URL:  http://localhost:30082"
        echo "  - To start Hybrid Proxy: python3 hybrid/failover_proxy.py"
        ;;

    test)
        echo -e "\n[+] Running Hybrid Failover & Self-Healing Test..."
        python3 scripts/test_failover.py
        ;;

    cost)
        echo -e "\n[+] Running Cost Optimization Analysis..."
        python3 scripts/cost_analysis.py
        ;;

    clean)
        echo -e "\n[!] Cleaning up clusters and containers..."
        docker compose down 2>/dev/null || true
        kind delete cluster --name private-cluster 2>/dev/null || true
        kind delete cluster --name public-cluster 2>/dev/null || true
        pkill -f "hybrid/failover_proxy.py" 2>/dev/null || true
        echo -e "[✓] Cleanup finished."
        ;;

    all|*)
        $0 compose
        $0 k8s
        ;;
esac
