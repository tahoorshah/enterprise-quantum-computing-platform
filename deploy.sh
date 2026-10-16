#!/usr/bin/env bash
#
# One-command deploy for the QFT Bank Quantum Computing Platform.
#   Minikube (Calico CNI) -> build images -> deploy all 12 workloads
#   -> wait for readiness -> (optional) Terraform IaC demo -> print access info.
#
# Usage:
#   ./deploy.sh         # full bringup (kubectl stack)
#   ./deploy.sh --tf    # also run the Terraform IaC demo (qft-terraform ns)
#   ./deploy.sh --down  # tear everything down
#
# Host prereqs: docker, minikube, kubectl (+ terraform for --tf).
set -euo pipefail
cd "$(dirname "$0")"

THIRD_PARTY_IMAGES="postgres:16-alpine redis:7-alpine prom/prometheus:v2.54.1 \
grafana/grafana:11.2.0 grafana/loki:3.1.1 grafana/promtail:3.1.1"

say(){ printf "\n\033[1;35m==> %s\033[0m\n" "$*"; }

if [[ "${1:-}" == "--down" ]]; then
  say "Tearing down"
  (cd infra/terraform && terraform destroy -refresh=false -auto-approve) 2>/dev/null || true
  kubectl delete -f infra/k8s/ --ignore-not-found 2>/dev/null || true
  say "Done. (Run 'minikube delete' to remove the cluster entirely.)"
  exit 0
fi

# 1. Cluster
if minikube status >/dev/null 2>&1; then
  say "Minikube already running"
else
  say "Starting Minikube (Calico CNI, so NetworkPolicies are enforced)"
  minikube start --driver=docker --cpus=4 --memory=8192 --cni=calico
fi

# 2. Images into Minikube's Docker (imagePullPolicy: Never)
say "Pointing Docker at Minikube and building images"
eval "$(minikube docker-env)"
export DOCKER_BUILDKIT=0          # this host's buildx can't boot buildkit; use the classic builder
for img in $THIRD_PARTY_IMAGES; do
  docker image inspect "$img" >/dev/null 2>&1 || docker pull "$img"
done
docker build -t qft-backend:latest  ./backend
docker build -t qft-frontend:latest ./frontend

# 3. Deploy the full stack
say "Applying all Kubernetes manifests (app + observability + network policies)"
kubectl apply -f infra/k8s/

say "Waiting for core data services"
kubectl rollout status deployment/postgres --timeout=180s
kubectl rollout status deployment/redis    --timeout=120s

say "Restarting backend so it reconnects to PostgreSQL, then waiting for all workloads"
kubectl rollout restart deployment/backend
kubectl rollout status deployment/backend  --timeout=180s
kubectl rollout status deployment/frontend --timeout=180s
kubectl wait --for=condition=ready pod --all --timeout=180s || true

# 4. Optional Terraform IaC demo
if [[ "${1:-}" == "--tf" ]]; then
  say "Terraform IaC demo (namespace qft-terraform)"
  ( cd infra/terraform && terraform init -input=false && terraform apply -refresh=false -auto-approve )
fi

# 5. Access info
MINIP=$(minikube ip)
say "Deployed. Cluster state:"
kubectl get pods
cat <<EOF

Access (tunnel these to your laptop):
  App         http://$MINIP:30080      login: admin / admin123  (analyst / analyst123)
  Prometheus  http://$MINIP:30090
  Grafana     http://$MINIP:30300      login: admin / admin

Laptop tunnel:
  ssh -i <key>.pem -L 8081:$MINIP:30080 -L 9091:$MINIP:30090 -L 3001:$MINIP:30300 ubuntu@<EC2_PUBLIC_IP>

Tear down:  ./deploy.sh --down
