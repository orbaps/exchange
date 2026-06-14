# Kind Cluster Setup for IICPC Platform

Local Kubernetes development cluster using [Kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker).

## Prerequisites

- **Docker** (or Podman) installed and running
- **Kind** installed: `brew install kind` / `choco install kind` / [download](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- **kubectl** installed: `brew install kubectl` / `choco install kubectl` / [download](https://kubernetes.io/docs/tasks/tools/)

## Quick Start

### 1. Create Cluster

```bash
# Linux/macOS
./scripts/kind-cluster.sh create

# Windows PowerShell
.\scripts\kind-cluster.ps1 create
```

This creates a 4-node cluster:
- **1 control-plane** (with ingress ports 80/443 mapped to localhost)
- **3 workers** with workload labels:
  - `workload=general` - hosting, evaluation, governance, strategic
  - `workload=botfleet` - bot fleet K8s Jobs
  - `workload=federation` - consensus, replication (stateful)

### 2. Build & Load Images

```bash
# Build all 7 service images
docker build -t iicpc-hosting:latest -f iac/docker/Dockerfile.hosting .
docker build -t iicpc-botfleet:latest -f iac/docker/Dockerfile.botfleet .
docker build -t iicpc-evaluation:latest -f iac/docker/Dockerfile.evaluation .
docker build -t iicpc-federation:latest -f iac/docker/Dockerfile.federation .
docker build -t iicpc-governance:latest -f iac/docker/Dockerfile.governance .
docker build -t iicpc-strategic:latest -f iac/docker/Dockerfile.strategic .
docker build -t iicpc-dashboard:latest -f iac/docker/Dockerfile.dashboard .

# Load into Kind
./scripts/kind-cluster.sh load-images
```

### 3. Verify Cluster

```bash
./scripts/kind-cluster.sh status
```

Expected output:
```
Nodes:
NAME                    STATUS   ROLES           AGE   VERSION
iicpc-control-plane     Ready    control-plane   2m    v1.29.2
iicpc-worker            Ready    <none>          2m    v1.29.2
iicpc-worker2           Ready    <none>          2m    v1.29.2
iicpc-worker3           Ready    <none>          2m    v1.29.2
```

## Port Mappings (Control Plane → Localhost)

| Service | Container Port | Localhost Port |
|---------|---------------|----------------|
| HTTP Ingress | 80 | 80 |
| HTTPS Ingress | 443 | 443 |
| gRPC | 30080 | 30080 |
| Grafana | 3000 | 3000 |
| Prometheus | 9090 | 9090 |
| Kafka | 30092 | 30092 |
| PostgreSQL | 30432 | 30432 |
| Redis | 30379 | 30379 |

## Accessing Services

### Dashboard (Frontend)
```
http://localhost
```

### API Services (via Ingress)
```
http://localhost/api/hosting/health
http://localhost/api/evaluation/health
```

### Grafana
```
http://localhost:3000
# Default: admin / prom-operator (check prometheus-stack values)
```

### Prometheus
```
http://localhost:9090
```

### Kafka (external)
```
bootstrap.servers=localhost:30092
```

### PostgreSQL/TimescaleDB
```
host=localhost port=30432 user=postgres password=postgres dbname=iicpc
```

### Redis
```
redis://localhost:30379
```

## Cluster Management

```bash
# Show status
./scripts/kind-cluster.sh status

# View logs
./scripts/kind-cluster.sh logs

# Delete cluster
./scripts/kind-cluster.sh delete
```

## Troubleshooting

### Cluster Creation Fails
```bash
# Check Docker resources (needs ~4GB RAM)
docker system df

# Increase Docker Desktop resources: Settings → Resources → Advanced
```

### Nodes Not Ready
```bash
# Check node conditions
kubectl describe nodes

# Common: CNI not ready - wait longer or restart
kind delete cluster --name iicpc && ./scripts/kind-cluster.sh create
```

### Images Not Found
```bash
# Build images first
docker images | grep iicpc

# Re-load after rebuild
./scripts/kind-cluster.sh load-images
```

### Port Conflicts
If ports 80/443/3000/9090 are in use:
1. Stop conflicting services
2. Or modify `kind-config.yaml` `extraPortMappings` to use different host ports

## Architecture Notes

### Node Labels for Scheduling
```yaml
# General workloads (API services)
nodeSelector:
  workload: general

# Bot fleet Jobs (high CPU burst)
nodeSelector:
  workload: botfleet

# Federation (stateful, consensus)
nodeSelector:
  workload: federation
```

### Resource Requests (Helm values)
```yaml
# General services
resources:
  requests: { cpu: "250m", memory: "512Mi" }
  limits: { cpu: "1000m", memory: "2Gi" }

# Bot fleet workers
resources:
  requests: { cpu: "500m", memory: "1Gi" }
  limits: { cpu: "2000m", memory: "4Gi" }

# Federation (stateful)
resources:
  requests: { cpu: "250m", memory: "1Gi" }
  limits: { cpu: "1000m", memory: "2Gi" }
```

## Next Steps

After cluster is running:
1. **Deploy Helm chart**: `helm install iicpc ./iac/helm/iicpc-platform -f values-kind.yaml`
2. **Verify deployments**: `kubectl get pods -n iicpc`
3. **Run tests**: `./scripts/kind-cluster.sh status`

## Useful Commands

```bash
# Shell into a pod
kubectl exec -it -n iicpc <pod-name> -- /bin/bash

# Port forward a service locally
kubectl port-forward -n iicpc svc/hosting 8000:8000

# View pod logs
kubectl logs -n iicpc -l app=hosting -f

# Scale deployment
kubectl scale deployment hosting -n iicpc --replicas=5
```