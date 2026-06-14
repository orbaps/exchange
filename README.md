<![CDATA[<div align="center">

<img src=".github/assets/banner.png" alt="IICPC Exchange Platform" width="100%" />

# IICPC Exchange

### The Open-Source Competitive Matching Engine Arena

[![CI](https://img.shields.io/github/actions/workflow/status/orbaps/exchange/ci.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/orbaps/exchange/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)](https://docker.com)
[![Kubernetes](https://img.shields.io/badge/k8s-native-326CE5.svg?logo=kubernetes&logoColor=white)](https://kubernetes.io)
[![Kafka](https://img.shields.io/badge/kafka-KRaft-231F20.svg?logo=apachekafka&logoColor=white)](https://kafka.apache.org)
[![gRPC](https://img.shields.io/badge/gRPC-protobuf-244c5a.svg?logo=google&logoColor=white)](https://grpc.io)

[**Docs**](docs/) · [**API Reference**](generated/api_docs.md) · [**Quick Start**](#-quick-start) · [**Contributing**](#-contributing) · [**Report Bug**](https://github.com/orbaps/exchange/issues)

</div>

---

**IICPC Exchange** is a production-grade distributed platform where contestants submit matching engine implementations that get sandboxed, stress-tested with deterministic bot fleets, validated against a reference engine, and ranked on a live leaderboard — all with nanosecond-precision fairness guarantees.

> **Think of it as**: A competitive arena for financial exchange engines — like competitive programming, but for order matching and trade execution.

<br/>

## ⚡ Why IICPC Exchange?

<table>
<tr>
<td width="50%">

### 🎯 &nbsp;Fair by Design
Every contestant gets identical compute, memory, and network resources. A centralized sequencer eliminates arrival-order variance. Shared-memory IPC ring buffers isolate engine latency from network jitter. No contestant has an unfair advantage.

</td>
<td width="50%">

### 🔬 &nbsp;Verified Correctness
Every submission is validated event-by-event against a golden-standard reference engine. Schema checks, state machine compliance, price-time priority verification, and full replay diffing — 8 layers of validation ensure no incorrect engine sneaks through.

</td>
</tr>
<tr>
<td width="50%">

### 🚀 &nbsp;Built for Scale
100K+ orders/sec sustained throughput. Distributed federation with Raft consensus. Multi-node execution with write-ahead logging. Kubernetes-native with Helm charts, Terraform IaC, and GitOps pipelines.

</td>
<td width="50%">

### 🏆 &nbsp;Full Competition Stack
Bracket tournaments (single/double elimination, Swiss, round-robin), seasonal campaigns, real-time leaderboards, multi-criteria grading (A+ to F), and a React dashboard with live WebSocket streaming.

</td>
</tr>
</table>

<br/>

## 📐 Architecture

```
                           ┌──────────────────────────────────┐
                           │        Contestant Upload         │
                           └──────────────┬───────────────────┘
                                          ▼
                           ┌──────────────────────────────────┐
                           │   Build Pipeline (scan + image)  │
                           └──────────────┬───────────────────┘
                                          ▼
┌──────────────┐    ┌──────────────────────────────────────────────────────┐
│              │    │              Runner Cluster (CPU-pinned)             │
│   Bot Fleet  │───▶│                                                      │
│  (seeded     │    │  ┌───────────┐    ┌──────────┐    ┌──────────────┐  │
│   PRNG)      │    │  │ Sequencer │───▶│ Gateway  │───▶│  Contestant  │  │
│              │    │  │ (SeqNo +  │    │  (IPC)   │    │  Sandbox     │  │
└──────────────┘    │  │  Journal) │    └──────────┘    │  (MicroVM)   │  │
                    │  └─────┬─────┘                    └──────┬───────┘  │
                    │        │                                 │          │
                    │        │         ┌──────────────┐        │          │
                    │        └────────▶│  Reference   │        │          │
                    │                  │  Engine      │        │          │
                    │                  └──────┬───────┘        │          │
                    └─────────────────────────┼────────────────┼──────────┘
                                              │                │
                                              ▼                ▼
                                     ┌────────────────────────────┐
                                     │   Validation Engine (diff) │
                                     └────────────┬───────────────┘
                                                  ▼
                    ┌─────────────┐    ┌───────────────────┐    ┌──────────────┐
                    │  Telemetry  │───▶│  Scoring Engine    │───▶│  Leaderboard │
                    │  Pipeline   │    │  (weighted rank)   │    │  (live)      │
                    └─────────────┘    └───────────────────┘    └──────────────┘
```

**Tech Stack:** Python 3.11+ · FastAPI · gRPC/Protobuf · Apache Kafka (KRaft) · PostgreSQL (TimescaleDB) · Redis · React 19 · Kubernetes · Terraform · Prometheus/Grafana

<br/>

## 🚀 Quick Start

### Using Docker Compose (recommended)

```bash
# Clone
git clone https://github.com/orbaps/exchange.git && cd exchange

# Install deps & compile protos
pip install -r requirements.txt
make proto

# Launch everything
docker-compose up -d
```

| Service | URL | Description |
|:---|:---|:---|
| 🖥️ Dashboard | [localhost:8080](http://localhost:8080) | Operator dashboard UI |
| 🔌 API Gateway | [localhost:8000](http://localhost:8000) | Main REST + gRPC API |
| 📊 Grafana | [localhost:3000](http://localhost:3000) | Monitoring dashboards |
| 📈 Prometheus | [localhost:9090](http://localhost:9090) | Metrics |

### Local Development

```bash
python -m venv .venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate                       # Linux/macOS

pip install -r requirements.txt
make proto

# Start infra only
docker-compose up -d postgres redis kafka

# Run a service
python -m uvicorn dashboard.app:app --port 8080 --reload
```

### Kubernetes (KIND)

```powershell
# Windows
.\scripts\kind-cluster.ps1

# Linux/macOS
./scripts/kind-cluster.sh
```

> 📘 See [KIND_CLUSTER.md](KIND_CLUSTER.md) for detailed cluster setup and troubleshooting.

<br/>

## 🧩 Project Overview

<details>
<summary><b>🔧 Core Engine</b> — The matching infrastructure</summary>

| Component | Description |
|:---|:---|
| [`gateway/`](gateway/) | IPC bridge — reads sequenced journal, delivers events to engines via shared-memory ring buffers |
| [`sequencer/`](sequencer/) | Assigns globally monotonic sequence numbers + nanosecond timestamps, journals to disk |
| [`execution/`](execution/) | Multi-threaded execution framework dispatching events to contestant sessions |
| [`scoring/`](scoring/) | Weighted composite scoring: 70% correctness, 15% latency, 10% throughput, 5% reliability |
| [`reference_engine/`](reference_engine/) | Golden-standard matching engine — FIFO, Pro-Rata, and Threshold Pro-Rata algorithms |
| [`contracts/`](contracts/) | Shared domain types (orders, trades, instruments, sessions) as Python dataclasses |
| [`proto/`](proto/) | Protobuf/gRPC schemas for inter-service communication |

</details>

<details>
<summary><b>📋 Submission Pipeline</b> — From upload to execution</summary>

| Component | Description |
|:---|:---|
| [`submission/`](submission/) | Validates structure (metadata.json + engine.py), AST-parses code, loads engines dynamically |
| [`validation/`](validation/) | Release hardening — determinism audits, security scans, dependency checks |
| [`validation_engine/`](validation_engine/) | Correctness engine — replay diffs, state machine compliance, price-time priority checks |
| [`sandbox/`](sandbox/) | Subprocess sandbox with resource limits (CPU, memory, timeout) |
| [`contestant_sandbox/`](contestant_sandbox/) | Production-grade Firecracker microVM isolation with CPU pinning + seccomp profiles |
| [`orchestration/`](orchestration/) | Autonomous cluster brain — anomaly detection, capacity forecasting, self-healing |

</details>

<details>
<summary><b>🏆 Competition Platform</b> — Tournaments, campaigns & leaderboards</summary>

| Component | Description |
|:---|:---|
| [`tournament/`](tournament/) | Multi-stage bracket tournaments (qualification → group → semifinal → final) |
| [`campaign/`](campaign/) | Benchmark campaign execution across multiple scenarios and contestants |
| [`leaderboard/`](leaderboard/) | Ranked leaderboard snapshots with tiebreaking, grades, and history |
| [`evaluation/`](evaluation/) | Deep evaluation — rule-based judging, adversarial testing, SHA-256 chained audit trail |
| [`benchmarking/`](benchmarking/) | Scenario-based benchmarking with certification (QPS, latency thresholds) |
| [`governance/`](governance/) | Autonomous governance — risk forecasting, policy evolution, approval workflows |
| [`strategic/`](strategic/) | Multi-cluster coordination — strategic planning across time horizons |

</details>

<details>
<summary><b>🤖 Load Generation</b> — Bot fleet & market simulation</summary>

| Component | Description |
|:---|:---|
| [`botfleet/`](botfleet/) | Deterministic bot fleet with 4 strategies: RandomTrader, MarketMaker, MomentumTrader, NoiseTrader |
| [`telemetry/`](telemetry/) | Latency distributions (p50–p99), throughput (EPS), failure rates, execution statistics |
| [`performance/`](performance/) | Platform self-testing: bottleneck detection, load testing, telemetry profiling |
| [`analytics/`](analytics/) | Platform-wide event bus (100+ event types) and analytics aggregation |

</details>

<details>
<summary><b>🖥️ Frontend & SDK</b> — Dashboard and contestant tools</summary>

| Component | Description |
|:---|:---|
| [`frontend/`](frontend/) | React 19 + TypeScript SPA — 22+ routes, WebSocket streaming, Recharts, Zustand state |
| [`dashboard/`](dashboard/) | FastAPI backend — 12 API routers, event bridge, journal-based state rebuild |
| [`sdk/`](sdk/) | Contestant SDK — C ABI engine interface, SPSC ring buffer, FFI engine loader |
| [`demo/`](demo/) | Deterministic demo runner with SHA-256 fingerprinted reproducibility |
| [`examples/`](examples/) | Sample contestant submission with metadata.json + engine.py template |

</details>

<details>
<summary><b>🌐 Federation & Infrastructure</b> — Distributed systems backbone</summary>

| Component | Description |
|:---|:---|
| [`federation/`](federation/) | Raft consensus, WAL replication, distributed scheduling, cryptographic signing, 8-step recovery |
| [`hosting/`](hosting/) | Container lifecycle management — build, deploy, run, monitor with resource quotas |
| [`iac/`](iac/) | Dockerfiles, Helm chart, Terraform modules (networking/k8s/storage/security/monitoring/backup) |
| [`gitops/`](gitops/) | Deployment sync + rollback management |
| [`dr/`](dr/) | Disaster recovery — cluster backup/restore, snapshot export/import |
| [`packaging/`](packaging/) | Deterministic submission package builder with SHA-256 fingerprints |

</details>

<br/>

## 🛠️ SDK — Build Your Engine

Contestants implement a matching engine as a **shared library** (.so/.dll) exporting three functions:

```c
// Initialize with instrument definitions
EngineHandle* engine_init(const InstrumentDefinition* instruments, uint32_t count);

// Process each inbound message, write ExecutionReports to outbound ring buffer
void engine_on_message(EngineHandle* handle, const JournalRecord* record, RingBufferWriter* out);

// Cleanup on shutdown
void engine_destroy(EngineHandle* handle);
```

The platform handles networking, sequencing, and IPC — **you only write the matching logic**.

### Submission Structure

```
my_submission/
├── metadata.json    # { "team_name": "...", "engine_class": "...", "version": "1.0" }
├── engine.py        # Your matching engine implementation
└── README.md        # Documentation
```

> 📘 See [`examples/`](examples/) for a complete working template.

### What Gets Tested

| Check | Description | Severity |
|:---|:---|:---|
| Schema validation | Required fields, enum ranges | Fatal |
| Sequence validation | Monotonic, gap-free output | Fatal |
| Order state invariant | `original_qty == cumulative_qty + leaves_qty + canceled_qty` | Fatal |
| State machine compliance | No illegal transitions (e.g., Filled → PartiallyFilled) | Fatal |
| Price-time priority | Earlier orders at same price fill first | Critical |
| Replay diff | Field-by-field comparison vs. reference engine | Critical |

<br/>

## 🧪 Testing

```bash
make test           # Full test suite with coverage
make test-quick     # Fast run, no coverage
make lint           # Ruff linter
make fmt            # Auto-format
make mypy           # Type checking
make all            # Everything: proto + lint + test + docker-build + helm-lint
```

24 test modules covering every component — from unit tests through integration and golden-test suites.

<br/>

## 🔄 CI/CD

| Workflow | Trigger | What it does |
|:---|:---|:---|
| **CI** | Push/PR to `main` | Protobuf lint → Python lint/test → Frontend checks → Docker build matrix → Helm lint |
| **CD** | Merge to `main` | Build + push images to GHCR → Deploy to KIND (dev) → Staging (Oracle Cloud) |
| **Release** | Tag push | Multi-arch build (amd64+arm64) → Helm chart package → GitHub Release |
| **Security** | Push/PR + weekly | Trivy scans → pip-audit → npm audit → CodeQL analysis |

<br/>

## 📚 Documentation

| Document | Description |
|:---|:---|
| [`docs/spec_v2.md`](docs/spec_v2.md) | Full platform specification (1800+ lines) — domain model, matching rules, state machines, replay design |
| [`docs/technical_design.md`](docs/technical_design.md) | Technical architecture deep-dive |
| [`generated/api_docs.md`](generated/api_docs.md) | Auto-generated API reference with examples |
| [`KIND_CLUSTER.md`](KIND_CLUSTER.md) | Local Kubernetes setup guide |
| [`docs/`](docs/) | Phase-by-phase development documentation (Phase 2.6 through 9.2) |

<br/>

## 🤝 Contributing

We welcome contributions! Here's the workflow:

```bash
# 1. Fork & clone
git clone https://github.com/YOUR_USERNAME/exchange.git && cd exchange

# 2. Set up dev environment
pip install -r requirements.txt
make proto

# 3. Create a branch
git checkout -b feat/my-feature

# 4. Make changes, test, lint
make test && make lint

# 5. Push & open a PR
git push origin feat/my-feature
```

### Makefile Reference

| Command | Description |
|:---|:---|
| `make init` | Install deps + compile protos |
| `make proto` | Compile .proto definitions |
| `make test` | Run tests with coverage |
| `make lint` | Lint with ruff |
| `make fmt` | Auto-format |
| `make docker-build` | Build all Docker images |
| `make helm-lint` | Validate Helm chart |
| `make kind-deploy` | Deploy to local KIND cluster |
| `make clean` | Remove build artifacts |

<br/>

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ for fair, deterministic, and scalable competitive benchmarking**

[⬆ Back to top](#iicpc-exchange)

</div>
]]>
