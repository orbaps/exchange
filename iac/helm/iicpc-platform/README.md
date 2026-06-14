# IICPC Platform Helm Chart

Helm chart for deploying the IICPC Summer Hackathon 2026 platform on Kubernetes.

## Overview

This Helm chart deploys the complete IICPC platform including:
- **Hosting Service**: Container management, deployment, and execution
- **Bot Fleet**: Distributed load generator with thousands of trading bots
- **Evaluation Service**: Benchmarking, scoring, and validation
- **Federation Service**: Consensus, replication, and distributed coordination
- **Governance Service**: Policy enforcement and risk management
- **Strategic Service**: Prediction and forecasting
- **Dashboard**: Frontend interface and real-time leaderboard

## Architecture

The platform consists of 7 microservices communicating via gRPC and Kafka:
- **Frontend**: React dashboard with WebSocket real-time updates
- **API Gateway**: Ingress controller with rate limiting
- **Core Services**: Hosting, Evaluation, Federation, Governance, Strategic
- **Infrastructure**: Redis, TimescaleDB, Kafka, Prometheus, Grafana, Loki, Tempo
- **Load Testing**: Bot fleet running as Kubernetes Jobs

## Quick Start

### Local Development (Kind)

```bash
# Create Kind cluster
./scripts/kind-cluster.sh create

# Build and load images
./scripts/kind-cluster.sh load-images

# Install Helm chart (using Kind values)
helm install iicpc ./iac/helm/iicpc-platform \
  -f ./iac/helm/iicpc-platform/values-kind.yaml

# Verify deployment
./scripts/kind-cluster.sh status
```

### Production (Oracle Cloud)

```bash
# Create Kubernetes cluster
# Install Helm
# Configure secrets and external services

helm install iicpc ./iac/helm/iicpc-platform \
  -f ./iac/helm/iicpc-platform/values-oracle.yaml \
  --set global.postgresql.enabled=true \
  --set global.redis.enabled=true \
  --set global.kafka.enabled=true \
  --set global.timescaledb.enabled=true \
  --set global.prometheus.enabled=true \
  --set global.grafana.enabled=true \
  --set global.loki.enabled=true \
  --set global.tempo.enabled=true \
  --set global.nginx-ingress.enabled=true \
  --set global.cert-manager.enabled=true
```

## Configuration

### Values Files

- **values.yaml**: Default production configuration
- **values-kind.yaml**: Optimized for local development with Kind
- **values-oracle.yaml**: Optimized for Oracle Cloud

### Key Configuration Options

#### Hosting Service
```yaml
hosting:
  replicaCount: 3
  image:
    repository: "ghcr.io/iicpc/iicpc-hosting"
    tag: "latest"
    pullPolicy: "IfNotPresent"
  service:
    type: "ClusterIP"
    ports:
      - name: http
        port: 8000
        targetPort: 8000
      - name: grpc
        port: 50051
        targetPort: 50051
  ingress:
    enabled: true
    className: "nginx"
    annotations:
      nginx.ingress.kubernetes.io/rate-limit: "100"
      nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    hosts:
      - host: "hosting.iicpc.local"
        paths:
          - path: /
            pathType: Prefix
    tls:
      - secretName: "hosting-tls"
        hosts:
          - "hosting.iicpc.local"
  resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 1Gi
  env:
    - name: KAFKA_BOOTSTRAP_SERVERS
      value: "kafka:9092"
    - name: REDIS_URL
      value: "redis://redis:6379/0"
    - name: TIMESCALEDB_DSN
      valueFrom:
        secretKeyRef:
          name: "iicpc-secrets"
          key: "TIMESCALEDB_DSN"
```

#### Bot Fleet
```yaml
botfleet:
  replicaCount: 3
  image:
    repository: "ghcr.io/iicpc/iicpc-botfleet"
    tag: "latest"
    pullPolicy: "IfNotPresent"
  service:
    type: "ClusterIP"
    ports:
      - name: http
        port: 8080
        targetPort: 8080
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 1000m
      memory: 2Gi
  env:
    - name: KAFKA_BOOTSTRAP_SERVERS
      value: "kafka:9092"
    - name: RESULTS_TOPIC
      value: "botfleet.results"
    - name: FLEET_CONFIG_PATH
      value: "/config/fleet-config.json"
```

#### Federation (Consensus)
```yaml
federation:
  replicaCount: 3
  image:
    repository: "ghcr.io/iicpc/iicpc-federation"
    tag: "latest"
    pullPolicy: "IfNotPresent"
  service:
    type: "ClusterIP"
    ports:
      - name: raft
        port: 50052
        targetPort: 50052
      - name: metrics
        port: 50053
        targetPort: 50053
  persistence:
    enabled: true
    size: 10Gi
    storageClass: "fast-ssd"
  resources:
    limits:
      cpu: 1000m
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 1Gi
  env:
    - name: NODE_ID
      valueFrom:
        fieldRef:
          fieldPath: "metadata.name"
    - name: CLUSTER_PEERS
      value: "federation-1:50052,federation-2:50052,federation-3:50052"
```

## Service Discovery

Services communicate via gRPC and Kafka:

- **gRPC Services**: Hosting, Evaluation, Governance, Strategic
- **Kafka Topics**:
  - `botfleet.events`: Bot events
  - `botfleet.results`: Bot results
  - `telemetry.raw`: Raw telemetry
  - `telemetry.aggregates`: Aggregated telemetry

## Monitoring

The platform includes comprehensive monitoring:

### Metrics
- **Prometheus**: Service metrics, latency, throughput
- **Grafana**: Dashboards for all services
- **Loki**: Logs aggregation
- **Tempo**: Distributed tracing

### Health Checks
All services expose health endpoints:
```bash
# Hosting health
http://hosting.iicpc.local/api/hosting/health

# Evaluation health
http://evaluation.iicpc.local/api/evaluation/health

# Governance health
http://governance.iicpc.local/api/governance/health
```

## Scaling

### Horizontal Pod Autoscaler
```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
```

### Bot Fleet Scaling
Bot fleet scales based on workload:
```yaml
botfleet:
  replicaCount: 3
  resources:
    limits:
      cpu: 2000m
      memory: 4Gi
    requests:
      cpu: 1000m
      memory: 2Gi
```

## Security

### TLS/SSL
- Cert-Manager for automatic TLS certificates
- Ingress controller with SSL passthrough
- Secrets management for database credentials

### Network Policy
```yaml
networkPolicy:
  enabled: true
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: "hosting"
        namespaceSelector:
          matchLabels:
            name: "iicpc"
```

## Backups

### Database Backups
```yaml
postgresql:
  backup:
    enabled: true
    schedule: "0 2 * * *"
    retention: 7

timescaledb:
  backup:
    enabled: true
    schedule: "0 3 * * *"
    retention: 30
```

## Troubleshooting

### Common Issues

#### Cluster Not Ready
```bash
# Check node status
kubectl get nodes

# Check pod status
kubectl get pods -A

# View logs
kubectl logs -n iicpc -l app=hosting -f
```

#### Service Not Accessible
```bash
# Check service endpoints
kubectl get svc -n iicpc

# Check ingress
kubectl get ingress -n iicpc

# Check logs
kubectl logs -n iicpc deployment/hosting
```

#### Scaling Issues
```bash
# Check pod autoscaler
kubectl get hpa -n iicpc

# Manually scale
kubectl scale deployment hosting -n iicpc --replicas=5
```

## Development

### Local Development
```bash
# Create Kind cluster
./scripts/kind-cluster.sh create

# Build and load images
./scripts/kind-cluster.sh load-images

# Install chart
helm install iicpc ./iac/helm/iicpc-platform \
  -f ./iac/helm/iicpc-platform/values-kind.yaml

# Watch deployments
watch -n 5 kubectl get pods -n iicpc
```

### Testing
```bash
# Run tests
helm test iicpc

# Lint chart
helm lint ./iac/helm/iicpc-platform

# Template test
helm template iicpc ./iac/helm/iicpc-platform \
  -f ./iac/helm/iicpc-platform/values-kind.yaml
```

## Production Deployment

### Pre-deployment Checklist
1. Configure external services (Oracle Cloud)
2. Create secrets for database credentials
3. Configure TLS certificates
4. Set up monitoring and alerting
5. Test in staging environment

### Deployment Steps
1. Deploy infrastructure (Oracle Cloud)
2. Install Helm chart with production values
3. Configure external services
4. Run smoke tests
5. Monitor and scale as needed

## Support

For issues and questions:
- GitHub Issues: https://github.com/iicpc/platform/issues
- Slack: #iicpc-platform (invite on request)
- Email: support@iicpc.example.com

## License

This Helm chart is licensed under MIT License. See LICENSE file for details.

## Acknowledgements

- Kubernetes (k8s)
- Helm
- Prometheus/Grafana ecosystem
- Strimzi Kafka Operator
- TimescaleDB Operator
- Cert-Manager
- NGINX Ingress Controller