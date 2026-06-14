<![CDATA[<div align="center">

# 🏛️ IICPC — Distributed Trading Benchmarking Platform

**A production-grade, cloud-native arena for benchmarking competitive matching engine implementations**

[![CI](https://github.com/orbap/exchange/actions/workflows/ci.yml/badge.svg)](https://github.com/orbap/exchange/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://docs.docker.com/compose/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-326CE5.svg)](https://kubernetes.io/)

---

*Contestants submit matching engine implementations. The platform builds, sandboxes, and stress-tests each submission using a deterministic bot fleet, validates correctness against a reference engine, and publishes live scores to a real-time leaderboard.*

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start (Docker Compose)](#quick-start-docker-compose)
  - [Development Setup](#development-setup)
  - [Local Kubernetes (KIND)](#local-kubernetes-kind)
- [Core Services](#-core-services)
- [Platform Components](#-platform-components)
- [SDK & Contestant Guide](#-sdk--contestant-guide)
- [Frontend & Dashboard](#-frontend--dashboard)
- [Federation & Distributed Execution](#-federation--distributed-execution)
- [Infrastructure & Deployment](#-infrastructure--deployment)
- [Testing](#-testing)
- [CI/CD Pipeline](#-cicd-pipeline)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌐 Overview

The IICPC (International Inter-Collegiate Programming Competition) Platform is a **distributed benchmarking arena** purpose-built for fairly evaluating trading matching engine implementations. It solves the fundamental challenges of competitive benchmarking:

| Challenge | How We Solve It |
|:---|:---|
| **Fair resource allocation** | MicroVM sandboxes with CPU pinning, identical resource limits |
| **Deterministic evaluation** | Centralized sequencer assigns global monotonic sequence numbers; seeded bot fleet |
| **Correctness validation** | Full event-level replay diff against a reference matching engine |
| **Latency isolation** | Shared-memory IPC ring buffers decouple engine performance from network jitter |
| **Live competition** | Real-time leaderboard, tournament brackets, WebSocket streaming |
| **Scale** | 100K+ orders/sec sustained; distributed federation for multi-node execution |

### How It Works

```
Contestant Upload
  → Build Pipeline (compile, scan, image)
  → Sandbox Deployment (isolated microVM)
  → Scenario Scheduler assigns seeds + rate plan
  → Bot Fleet generates deterministic OrderRequests
  → Sequencer assigns SeqNo + LogicalTimestamp, journals to disk
  → Sequenced stream delivered via IPC ring buffer to:
      ├── Contestant Engine (produces ExecutionReports)
      └── Reference Engine  (produces ExecutionReports)
  → Validation Engine diffs both output streams
  → Telemetry Pipeline (metrics + tracing)
  → Scoring Engine computes composite rank
  → Leaderboard streams live to UI
```

---

## ✨ Key Features

### Competition Engine
- **Multi-algorithm matching**: FIFO (NASDAQ-style), Pro-Rata (CME-style), Threshold Pro-Rata hybrid
- **Full order types**: Limit, Market, Stop-Limit with IOC/FOK/GFD/GTC time-in-force
- **Exchange sessions**: PreOpen → Continuous → Halt → Close lifecycle with auction uncrossing
- **Self-Match Prevention**: CancelNewest, CancelOldest, CancelBoth modes
- **Deterministic replay**: Bit-identical replays from journaled event streams

### Platform
- **Bracket tournaments**: Single-elimination, double-elimination, round-robin, Swiss
- **Campaign seasons**: Time-bounded competitive events with enrollment and scheduling
- **Real-time leaderboard**: Redis-backed rankings with historical tracking
- **Analytics pipeline**: Trade metrics, VWAP, volatility, performance profiling
- **Governance**: Rule enforcement, compliance checking, community voting

### Infrastructure
- **Federation**: Raft-inspired consensus, write-ahead logging, distributed scheduling
- **Observability**: Prometheus metrics, distributed tracing, structured logging
- **Cloud-native**: Kubernetes manifests, Helm charts, Terraform IaC (GKE/OKE)
- **Disaster recovery**: Automated backups, point-in-time recovery, snapshot export/import

---

## 🏗 Architecture

The platform follows a **microservices architecture** with event-driven communication:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Control Plane Cluster                          │
│                                                                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────────┐           │
│  │ Dashboard │  │ Hosting   │  │ Scoring  │  │ Leaderboard│           │
│  │ (React)  │  │ Service   │  │ Engine   │  │ Engine     │           │
│  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └─────┬──────┘           │
│       │              │              │              │                   │
│       └──────────────┼──────────────┼──────────────┘                   │
│                      │         ┌────┴─────┐                            │
│                      │         │  Kafka   │                            │
│                      │         └────┬─────┘                            │
│                      │              │                                  │
│  ┌──────────┐  ┌─────┴─────┐  ┌────┴──────┐  ┌───────────┐          │
│  │ BotFleet │  │ Sequencer │  │ Validator │  │ Telemetry │          │
│  │ Workers  │  │           │  │ Engine    │  │ Pipeline  │          │
│  └────┬─────┘  └─────┬─────┘  └───────────┘  └───────────┘          │
│       │              │                                                │
├───────┼──────────────┼────────────────────────────────────────────────┤
│       │     Runner Cluster (CPU-pinned, no internet egress)           │
│       │              │                                                │
│  ┌────┴─────┐  ┌─────┴─────┐  ┌──────────────┐                      │
│  │ Bot Fleet│  │  Gateway  │  │  Reference   │                      │
│  │ (bots)   │→ │  (IPC)    │→ │  Engine      │                      │
│  └──────────┘  └─────┬─────┘  └──────────────┘                      │
│                      │                                                │
│                ┌─────┴──────────┐                                     │
│                │  Contestant    │                                     │
│                │  Sandbox       │                                     │
│                │  (Firecracker) │                                     │
│                └────────────────┘                                     │
└─────────────────────────────────────────────────────────────────────────┘
         │              │                │
    ┌────┴────┐   ┌─────┴─────┐   ┌──────┴──────┐
    │ Redis   │   │ PostgreSQL│   │   Kafka     │
    │ Cache   │   │ (Timescale│   │  (KRaft)    │
    └─────────┘   └───────────┘   └─────────────┘
```

### Technology Stack

| Layer | Technology |
|:---|:---|
| **Language** | Python 3.11+ |
| **Web Framework** | FastAPI + Uvicorn |
| **Frontend** | React 19 + TypeScript + Vite |
| **Inter-service RPC** | gRPC + Protocol Buffers |
| **Message Broker** | Apache Kafka (KRaft mode) |
| **Database** | PostgreSQL (TimescaleDB) |
| **Cache** | Redis 7 |
| **Container Runtime** | Docker |
| **Orchestration** | Kubernetes (Helm) |
| **IaC** | Terraform (GKE/OKE) + Pulumi |
| **CI/CD** | GitHub Actions |
| **Observability** | Prometheus + Grafana + OpenTelemetry |
| **State Management** | Zustand (frontend) |
| **Charts** | Recharts |

---

## 📁 Project Structure

```
IICPC Project/
├── 🔧 Core Services
│   ├── gateway/              # API Gateway — entry point for all external requests
│   ├── sequencer/            # Deterministic order sequencing (gRPC)
│   ├── execution/            # Trade execution engine (order matching)
│   ├── scoring/              # Multi-dimensional scoring with pluggable strategies
│   ├── contracts/            # Shared data contracts (Pydantic models)
│   └── proto/                # Protocol Buffer definitions + generated stubs
│
├── 📋 Submission Pipeline
│   ├── submission/           # Code submission processing + anti-cheat
│   ├── validation/           # Multi-layer validation pipeline
│   ├── validation_engine/    # Runtime behavior validation (sandboxed execution)
│   ├── sandbox/              # Kubernetes-native sandboxed execution
│   ├── contestant_sandbox/   # Contestant-facing sandbox management
│   └── orchestration/        # Full submission lifecycle coordinator
│
├── 🏆 Competition Features
│   ├── tournament/           # Bracket-based tournament system
│   ├── campaign/             # Time-bounded competitive seasons
│   ├── leaderboard/          # Real-time ranking engine (Redis)
│   ├── evaluation/           # Multi-criteria strategy grading (A+ to F)
│   ├── benchmarking/         # Strategy benchmarking against market scenarios
│   ├── governance/           # Rule enforcement, compliance, voting
│   └── strategic/            # Reference trading strategies (momentum, mean-reversion, market-making)
│
├── 🤖 Market Simulation
│   ├── botfleet/             # Automated bot fleet for market liquidity
│   ├── reference_engine/     # Golden-standard matching engine for validation
│   └── demo/                 # Deterministic demo runner for showcases
│
├── 📊 Observability
│   ├── analytics/            # Trade analytics pipeline (VWAP, volatility)
│   ├── telemetry/            # Prometheus metrics + distributed tracing
│   └── performance/          # Load testing + profiling framework
│
├── 🖥️ User Interface
│   ├── frontend/             # React 19 + TypeScript SPA (operator dashboard)
│   ├── dashboard/            # FastAPI backend API powering the dashboard
│   └── sdk/                  # Contestant SDK (C ABI interfaces + ring buffers)
│
├── 🌐 Federation
│   ├── federation/           # Distributed consensus, replication, scheduling
│   ├── federation_run_artifacts/  # Federation test run outputs
│   └── federation_run_replica/    # Per-node replica storage (WAL, snapshots)
│
├── 🚀 Deployment & Infrastructure
│   ├── iac/                  # Infrastructure as Code
│   │   ├── docker/           # Dockerfiles for all services
│   │   ├── helm/             # Helm chart (iicpc-platform)
│   │   ├── terraform/        # Terraform modules + environments
│   │   └── gitops/           # ArgoCD + Flux configurations
│   ├── gitops/               # Python GitOps module (deployment sync, rollback)
│   ├── hosting/              # Container orchestration + resource quotas
│   ├── packaging/            # Submission package builder (SHA-256 fingerprinted)
│   ├── dr/                   # Disaster recovery (backup/restore)
│   └── scripts/              # Setup + deployment scripts
│
├── 📚 Documentation & Tooling
│   ├── docs/                 # Phase documentation + specs + technical design
│   ├── docs_generator/       # Deterministic documentation generator
│   ├── generated/            # Auto-generated API docs + gRPC stubs
│   ├── examples/             # Example contestant submissions
│   └── tests/                # Test suite (24 modules)
│
├── ⚙️ Configuration
│   ├── docker-compose.yml    # Full local development stack
│   ├── kind-config.yaml      # Local Kubernetes cluster configuration
│   ├── Makefile              # Build automation targets
│   ├── pyproject.toml        # Python project + dependency management
│   └── requirements.txt      # pip-installable dependencies
│
└── 📖 Documentation Files
    ├── README.md             # ← You are here
    └── KIND_CLUSTER.md       # Local Kubernetes setup guide
```

---

## 🚀 Getting Started

### Prerequisites

| Tool | Minimum Version | Purpose |
|:---|:---|:---|
| **Python** | 3.11+ | Core runtime |
| **Docker** | 24+ | Container builds |
| **Docker Compose** | 2.0+ | Local development stack |
| **Git** | 2.30+ | Version control |
| **KIND** | 0.20+ | Local Kubernetes (optional) |
| **kubectl** | 1.28+ | Kubernetes CLI (optional) |
| **Helm** | 3.12+ | Chart deployment (optional) |
| **Node.js** | 18+ | Frontend development (optional) |

### Quick Start (Docker Compose)

The fastest way to get the full platform running locally:

```bash
# 1. Clone the repository
git clone https://github.com/orbap/exchange.git
cd exchange

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Compile Protocol Buffers
make proto

# 4. Start the full stack (all services + infrastructure)
docker-compose up -d

# 5. Verify everything is running
docker-compose ps
```

**Services will be available at:**

| Service | URL | Description |
|:---|:---|:---|
| Dashboard UI | http://localhost:8080 | Operator dashboard |
| Hosting API | http://localhost:8000 | Main API gateway |
| Evaluation | http://localhost:8001 | Evaluation service |
| Federation | http://localhost:8002 | Federation endpoints |
| Governance | http://localhost:8003 | Governance API |
| Strategic | http://localhost:8004 | Strategic analytics |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3000 | Monitoring dashboards |

### Development Setup

For local development without Docker:

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Compile Protocol Buffers
make proto

# 4. Start infrastructure services only
docker-compose up -d postgres redis kafka

# 5. Run any individual service
python -m uvicorn dashboard.app:app --port 8080 --reload
```

### Local Kubernetes (KIND)

For a full Kubernetes-native deployment on your local machine:

```powershell
# Windows
.\scripts\kind-cluster.ps1
```

```bash
# Linux/macOS
./scripts/kind-cluster.sh
```

See [KIND_CLUSTER.md](KIND_CLUSTER.md) for detailed setup instructions, port mappings, and troubleshooting.

---

## ⚙️ Core Services

### Gateway

The **API Gateway** is the single entry point for all external requests.

- **Port**: 8000 (HTTP) + 50051 (gRPC)
- **Features**: REST API, rate limiting (100 req/min per key), API key authentication, Redis caching
- **Endpoints**: Order submission, order book queries, recent trades, health checks
- **Communication**: Publishes to Kafka `orders` topic, calls Sequencer via gRPC

### Sequencer

**Deterministic order sequencing** for fairness — assigns globally unique, monotonically increasing sequence numbers.

- **Port**: 50051 (gRPC)
- **Guarantees**: Gap-free sequencing, journal-before-delivery persistence
- **Performance target**: ≥ 500,000 msg/sec, < 5µs p99 latency
- **Output**: Publishes to Kafka `sequenced_orders` topic

### Execution Engine

**Price-time priority order matching** with bid/ask order books.

- **Port**: 8002
- **Algorithm**: Configurable FIFO / Pro-Rata / Threshold Pro-Rata
- **Input**: Consumes `sequenced_orders` from Kafka
- **Output**: Publishes trades to Kafka `trades` topic

### Scoring Engine

**Multi-dimensional scoring** with pluggable strategy system.

- **Port**: 8003
- **Default weights**: P&L (40%), Sharpe ratio (25%), max drawdown (15%), win rate (10%), volume (10%)
- **Input**: Consumes trades from Kafka
- **Output**: Updates Redis-backed leaderboard

### Contracts & Proto

**Shared domain model** used across all services:

- `contracts/` — Pydantic models for `Order`, `Trade`, `OrderBook`, `Contestant`, `Submission`, `Score`
- `proto/` — gRPC service definitions (`OrderSequencer`) and message types

---

## 🏆 Platform Components

### Tournament System

Full bracket-based competition management:

```
Create Tournament → Open Registration → Generate Bracket
→ Schedule Matches → Run Rounds → Advance Winners → Final
```

- **Bracket types**: Single/double elimination, round-robin, Swiss
- **Features**: Seeding, venue assignment, break scheduling, Kafka event publishing

### Campaign System

Time-bounded competitive seasons:

- **Lifecycle**: Draft → Active → Paused → Completed → Archived
- **Features**: Contestant enrollment, submission tracking, auto-activation/completion by schedule

### Leaderboard Engine

Redis-sorted-set real-time rankings:

- **Time frames**: Hourly, daily, weekly, all-time
- **Features**: Score history, pagination, multi-competition support

### Evaluation Framework

Multi-criteria strategy assessment producing letter grades (A+ to F):

- **Profitability**: P&L, ROI, profit factor
- **Risk**: Sharpe ratio, Sortino ratio, VaR, max drawdown
- **Execution**: Win rate, trade frequency, average duration
- **Consistency**: Equity curve smoothness, streak analysis

### Benchmarking

Strategy evaluation against standardized market scenarios:

- **Scenarios**: Bull market, bear market, high volatility, flash crash, steady growth
- **Metrics**: P&L, Sharpe ratio, max drawdown, win rate, total trades

### Governance

Platform rule enforcement and community governance:

- **Rule types**: Trading limits, position limits, rate limits, content policy, fair play
- **Features**: Compliance checking, violation tracking, voting on proposals

---

## 🛠 SDK & Contestant Guide

### Contestant SDK

Contestants implement a matching engine as a **shared library** exporting three C ABI functions:

```c
// Called once at startup with instrument definitions
EngineHandle* engine_init(
    const InstrumentDefinition* instruments,
    uint32_t instrument_count
);

// Called for each inbound message (NewOrder, Cancel, Replace, SessionTransition)
// Must write ExecutionReports to the outbound ring buffer
void engine_on_message(
    EngineHandle* handle,
    const JournalRecord* record,
    RingBufferWriter* outbound
);

// Called at shutdown for cleanup
void engine_destroy(EngineHandle* handle);
```

The platform provides the gateway, networking, and IPC — contestants only implement the **matching core**.

### Shared-Memory Ring Buffer

Communication uses a **wait-free SPSC ring buffer** (single-producer, single-consumer):

```
Gateway → [Inbound Ring Buffer] → Contestant Engine
Contestant Engine → [Outbound Ring Buffer] → Validator
```

This eliminates network jitter from latency measurements.

### Example Submission Structure

```
my_submission/
├── metadata.json       # Team name, engine class, version
├── engine.py           # Matching engine implementation
└── README.md           # Documentation
```

See the `examples/contestant_submission/` directory for a complete template.

---

## 🖥️ Frontend & Dashboard

### React Frontend (Operator Dashboard)

A React 19 + TypeScript SPA built with Vite:

- **22+ routes**: Overview, Leaderboard, Tournament, Deployments, Analytics, Operations, Replay Viewer, Governance, Forecasting, Risk, Simulation, Strategic, Multi-Cluster, Recovery, and more
- **Real-time updates**: WebSocket streaming for leaderboard, analytics, tournament, and health channels
- **State management**: Zustand stores for auth, dashboard, and replay state
- **Charts**: Recharts for data visualization

### Dashboard API (FastAPI Backend)

The backend powering the dashboard:

- **12 API router modules**: Auth, public data, admin controls, WebSocket, replay, evaluation, federation, governance, strategic, cloud ops, benchmarking, release management
- **Event-driven**: EventBridge + ChannelManager for real-time state propagation
- **Journal-based**: Auto-rebuilds state from JSONL journals on startup

### Default Credentials

| Role | Username | Description |
|:---|:---|:---|
| Admin | `admin` | Full platform access |
| Judge | `judge` | Evaluation and scoring |
| Public | `public` | Read-only leaderboard view |

---

## 🌐 Federation & Distributed Execution

The federation layer enables **multi-node competition execution** with strong consistency:

### Consensus

- **Raft-inspired leader election** with monotonic terms and lexicographic tie-breaking
- **States**: Follower → Candidate → Leader
- **Heartbeat + lease-based** leadership management

### Replication

- **Write-Ahead Log (WAL)**: Hash-chained, integrity-verified on replay
- **AppendEntries RPC**: Log replication from leader to followers
- **Majority commit**: Entries committed once acknowledged by quorum

### Scheduling

- **4 scheduling modes**: Round-robin, least-loaded, capability-match, random-seeded
- **Partitioned execution**: Benchmarks split and dispatched across federated workers

### Recovery

8-step recovery procedure:
1. Load Snapshot → 2. Verify Hash → 3. Replay WAL → 4. Rebuild Consensus Log →
5. Restore Scheduler → 6. Restore Registry → 7. Restore Locks → 8. Validate Quorum

### Security

- **HMAC-based message authentication** between federation nodes
- **Cryptographic signatures** on all inter-node communication

---

## 🚢 Infrastructure & Deployment

### Docker

All services have individual Dockerfiles in `iac/docker/`:

```bash
# Build all images
make docker-build

# Start full stack
docker-compose up -d

# Stop
docker-compose down
```

### Kubernetes (Helm)

Deploy to any Kubernetes cluster using the Helm chart:

```bash
# Lint the chart
make helm-lint

# Template (dry run)
make helm-template

# Deploy to KIND
make kind-deploy
```

The Helm chart (`iac/helm/iicpc-platform/`) includes templates for all services, ingress, RBAC, and resource quotas.

### Terraform

Production infrastructure on GKE or OKE:

```bash
cd iac/terraform/environments/dev
terraform init
terraform plan
terraform apply
```

**Modules**: Networking, Kubernetes cluster, storage, security, monitoring, backup.

### GitOps

Supports both **ArgoCD** and **Flux** for continuous deployment:

- Configurations in `iac/gitops/argocd/` and `iac/gitops/flux/`
- Python GitOps module (`gitops/`) provides deployment sync and rollback capabilities

### Disaster Recovery

- **Automated backups**: PostgreSQL (pg_dump), Redis (BGSAVE), filesystem
- **Point-in-time recovery**: Restore from any backup with health verification
- **Configurable retention**: Default 7-day backup retention

---

## 🧪 Testing

The test suite covers 24+ modules matching every service component:

```bash
# Run all tests with coverage
make test

# Quick test (no coverage)
make test-quick

# Run specific module tests
pytest tests/test_scoring.py -v
pytest tests/federation/ -v
pytest tests/tournament/ -v
```

### Test Categories

| Directory | Tests |
|:---|:---|
| `tests/analytics/` | Analytics pipeline |
| `tests/benchmarking/` | Benchmark runner + scenarios |
| `tests/botfleet/` | Bot fleet management |
| `tests/campaign/` | Campaign lifecycle |
| `tests/determinism/` | Replay determinism verification |
| `tests/evaluation/` | Strategy evaluation grading |
| `tests/execution/` | Order matching engine |
| `tests/federation/` | Consensus, replication, recovery |
| `tests/golden/` | Golden-test reference validation |
| `tests/governance/` | Rule enforcement |
| `tests/hosting/` | Container management |
| `tests/integration/` | End-to-end integration |
| `tests/orchestration/` | Submission pipeline |
| `tests/sandbox/` | Sandbox execution |
| `tests/strategic/` | Trading strategies |
| `tests/submission/` | Code submission processing |
| `tests/tournament/` | Tournament brackets |
| `tests/validation/` | Validation pipeline |
| `tests/validation_engine/` | Runtime validation |

### Linting & Formatting

```bash
# Lint
make lint

# Format
make fmt

# Type checking
make mypy
```

---

## 🔄 CI/CD Pipeline

Four GitHub Actions workflows automate the full lifecycle:

### CI (`ci.yml`)

Triggered on push/PR to `main`:
1. **Protobuf lint** — buf linter
2. **Python checks** — ruff lint, pytest with coverage, codecov upload
3. **Frontend checks** — npm install + lint
4. **Docker build** — Matrix build of all 7 service images
5. **Helm lint** — Chart validation

### CD (`cd.yml`)

Triggered on merge to `main`:
1. Builds and pushes all images to **GHCR** (GitHub Container Registry)
2. Deploys to KIND (dev environment)
3. Oracle Cloud staging deployment (configurable)

### Release (`release.yml`)

Triggered on tag push:
1. **Multi-arch builds** (amd64 + arm64)
2. **Helm chart packaging**
3. **GitHub Release** creation with artifacts

### Security (`security.yml`)

Runs on push/PR + weekly schedule:
1. **Trivy** container vulnerability scanning
2. **pip-audit** for Python dependency CVEs
3. **npm audit** for frontend dependencies
4. **CodeQL** analysis for code security

---

## 📡 API Reference

### Gateway REST API

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/v1/orders` | Submit a new order |
| `GET` | `/api/v1/orderbook/{symbol}` | Get order book for a symbol |
| `GET` | `/api/v1/trades/recent` | Get recent trades |
| `GET` | `/health` | Health check |

### WebSocket

```
ws://localhost:8000/api/ws
```

Channels: `leaderboard`, `analytics`, `tournament`, `health`

### Dashboard API

| Module | Base Path | Description |
|:---|:---|:---|
| Auth | `/api/auth/` | JWT authentication |
| Public | `/api/public/` | Leaderboard, tournament, analytics |
| Admin | `/api/admin/` | Tournament control, state rebuild |
| WebSocket | `/ws` | Real-time streaming |
| Replay | `/api/replay/` | Event replay |
| Evaluation | `/api/evaluation/` | Evaluation management |
| Federation | `/api/federation/` | Federation control |
| Governance | `/api/governance/` | Rule management |
| Strategic | `/api/strategic/` | Strategic analytics |
| Cloud | `/api/cloud/` | Cloud operations |
| Benchmarking | `/api/benchmarking/` | Benchmark runs |
| Release | `/api/release/` | Release management |

### Rate Limiting

- **100 requests/minute** per API key (token-bucket algorithm)
- Returns `429 Too Many Requests` when exceeded

See `generated/api_docs.md` for the complete API reference with request/response examples.

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|:---|:---|:---|
| `REDIS_URL` | `redis://localhost:6379` | Redis connection |
| `KAFKA_BOOTSTRAP` | `localhost:9092` | Kafka broker |
| `DATABASE_URL` | `postgresql://exchange:exchange@localhost/exchange` | PostgreSQL connection |
| `GATEWAY_PORT` | `8000` | Gateway HTTP port |
| `SEQUENCER_PORT` | `50051` | Sequencer gRPC port |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Hosting Profiles

Pre-built deployment profiles in `hosting/config.py`:

| Profile | Replicas | CPU | Memory | Auto-scale |
|:---|:---|:---|:---|:---|
| **Development** | 1 | 0.5 cores | 512 MB | ✗ |
| **Staging** | 2 | 1 core | 1 GB | 2–4 |
| **Production** | 3 | 2 cores | 4 GB | 3–10 |

---

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory, organized by development phase:

| Phase | Document | Topic |
|:---|:---|:---|
| Spec | `docs/spec_v2.md` | Full platform specification (68KB) |
| Design | `docs/technical_design.md` | Technical architecture (89KB) |
| 2.6 | Reference Engine Completion | Golden-standard matching engine |
| 3.x | Contestant Submission, Campaigns, Sandbox, Telemetry, Scoring | Core competition pipeline |
| 4.x | Leaderboard, Bot Fleet, Workers, Streaming, Hosting, Tournament | Platform features |
| 6.0 | Autonomous Evaluation | Automated evaluation framework |
| 7.x | Federation, HA, Consensus Replication | Distributed execution |
| 8.x | Cluster Orchestration, Predictive Ops, Strategic Planning | Autonomous operations |
| 9.x | Cloud Deployment, Production Benchmarking, Release Hardening | Production readiness |

### Generating Documentation

```bash
# Generate API reference and architecture docs
python -m docs_generator.generator
```

Output is written to the `generated/` directory with SHA-256 fingerprints for reproducibility.

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

### Development Workflow

1. **Fork** the repository
2. **Create a branch** for your feature or fix
3. **Set up** the development environment (see [Development Setup](#development-setup))
4. **Write tests** for your changes
5. **Run the full test suite**: `make test`
6. **Lint your code**: `make lint`
7. **Submit a pull request**

### Make Targets Reference

| Target | Description |
|:---|:---|
| `make init` | Install dependencies + compile protos |
| `make proto` | Compile Protocol Buffer definitions |
| `make test` | Run tests with coverage |
| `make test-quick` | Run tests without coverage |
| `make lint` | Run ruff linter |
| `make fmt` | Run ruff formatter |
| `make mypy` | Run type checker |
| `make docker-build` | Build all Docker images |
| `make helm-lint` | Validate Helm chart |
| `make kind-create` | Create local KIND cluster |
| `make kind-deploy` | Deploy to KIND cluster |
| `make clean` | Remove build artifacts |
| `make all` | Full build pipeline |

### Project Conventions

- **Python**: 3.11+, typed with Pydantic models, async/await patterns
- **Testing**: pytest + pytest-asyncio, aim for comprehensive coverage
- **Docs**: Docstrings on all public APIs, phase documents for major features
- **Commits**: Conventional commit messages preferred

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built for fair, deterministic, and scalable competitive benchmarking** 🏛️

[Documentation](docs/) · [API Reference](generated/api_docs.md) · [Examples](examples/) · [Report Issues](https://github.com/orbap/exchange/issues)

</div>
]]>
