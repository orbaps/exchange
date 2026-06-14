<![CDATA[<div align="center">

<img src=".github/assets/banner.png" alt="IICPC Exchange Platform" width="100%" />

# 🏛️ IICPC Exchange Platform

**Official Submission for the IICPC Summer Hackathon 2026**

[![CI Status](https://img.shields.io/github/actions/workflow/status/orbaps/exchange/ci.yml?branch=main&label=Build&logo=githubactions&logoColor=white&style=for-the-badge)](https://github.com/orbaps/exchange/actions)
[![Python Version](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white&style=for-the-badge)](https://python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Native-326CE5.svg?logo=kubernetes&logoColor=white&style=for-the-badge)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

[**Documentation**](docs/) · [**API Reference**](generated/api_docs.md) · [**Quick Start**](#-getting-started) · [**Hackathon Deliverables**](#-expected-deliverables)

</div>

---

## ☀️ IICPC Summer Hackathon 2026

*Running from May 9th to June 10th, 2026.*

This competition is designed for top-tier systems engineers, competitive programmers, and algorithmic thinkers. At IICPC, we champion hardcore engineering excellence. This is not a standard "demo-to-win" hackathon; it demands high-performance code, system resilience, and a deep understanding of scale and distributed systems. Every technical decision in this repository is backed by a deliberate, well-reasoned architectural thought process.

### 🎯 The Challenge

The objective is to architect and build a **Distributed Benchmarking and Hosting Platform** designed to evaluate contestant-submitted trading infrastructure. 

The platform allows contestants to upload their core code (matching engines/simulated orderbooks). The system securely hosts this submission, exposes endpoints, and dynamically spawns a massive, distributed fleet of "trading bots" to bombard the system with concurrent orders, simulating peak market volatility. Finally, the platform captures granular telemetry to assess the submitted code on latency, throughput, and correctness, streaming the results to a live, dynamic leaderboard.

---

## 🏗️ Architectural Components & Requirements

Our solution directly addresses and exceeds the hackathon's core requirements, implementing a highly concurrent, resilient, and decoupled microservices architecture.

<table width="100%">
<tr>
<td width="50%">

### 1️⃣ Submission & Sandboxing Engine
**Requirement:** Secure pipeline for code upload, containerized deployment, strict isolation, and fair resource allocation.

**Our Implementation:**
- **Firecracker MicroVMs:** Untrusted contestant code runs in hardware-isolated microVMs (`contestant_sandbox/`).
- **Resource Fairness:** Strict cgroup memory/IO limits, CPU pinning (`isolcpus`), and disabled SMT. No noisy neighbors.
- **Zero-Jitter IPC:** Network latency is decoupled from engine latency. Sequenced events are delivered via **wait-free SPSC shared-memory ring buffers**.

</td>
<td width="50%">

### 2️⃣ Distributed Load Generator (Bot Fleet)
**Requirement:** Scalable traffic generation spawning thousands of bots simulating diverse market participants (Limit/Market/Cancels).

**Our Implementation:**
- **Seeded PRNG Bot Fleet:** Generates **100,000+ orders/second** (`botfleet/`). Bots execute configurable strategies (Market Making, Momentum, Noise) mapped to realistic market regimes.
- **Absolute Determinism:** A centralized **Sequencer** assigns globally monotonic sequence numbers and nanosecond logical timestamps to all incoming orders. Arrival-order variance is mathematically eliminated.

</td>
</tr>
<tr>
<td width="50%">

### 3️⃣ Telemetry & Validation Ingester
**Requirement:** Low-latency tracking for latency (p50, p90, p99), throughput (TPS), and correctness (price-time priority, fill accuracy).

**Our Implementation:**
- **Golden Reference Engine:** Every submission is diffed event-by-event against our built-in `reference_engine/` (supporting FIFO, Pro-Rata).
- **Deep Validation:** Enforces state machine compliance, quantity conservation, and strict price-time priority (`validation_engine/`).
- **Telemetry Pipeline:** Granular latency profiling and throughput tracking separated from network jitter (`telemetry/`).

</td>
<td width="50%">

### 4️⃣ Real-Time Leaderboard & Analytics
**Requirement:** Frontend streaming live metrics, ranking contestants dynamically on speed, stability, and algorithmic accuracy.

**Our Implementation:**
- **Composite Scoring Engine:** Weights correctness (70%), latency (15%), throughput (10%), and reliability (5%) (`scoring/`).
- **React 19 SPA:** Operator dashboard connected via WebSockets for sub-second live updates (`frontend/`, `dashboard/`).
- **Redis-Backed Leaderboard:** Real-time ranking with historical time-series tracking (`leaderboard/`).

</td>
</tr>
</table>

---

## 📦 Expected Deliverables

We have fully delivered on the required Hackathon assets:

1. ✅ **Working Infrastructure Prototype:** A fully functional platform demonstrating the complete pipeline (Upload → Deployment → Load Testing → Scoring). See [Getting Started](#-getting-started) to run the full stack via `docker-compose`.
2. ✅ **Architecture Blueprint:** A comprehensive system design document detailing microservices, gRPC/Kafka inter-service communication, TimescaleDB/Redis data stores, and Firecracker isolation. See the [Architecture section below](#-system-architecture) and the full [`docs/technical_design.md`](docs/technical_design.md).
3. ✅ **Infrastructure as Code (IaC):** Automated deployment scripts proving horizontal scalability in a modern cloud environment. See the [`iac/`](iac/) directory for our complete **Terraform**, **Kubernetes (Helm)**, and **GitOps (ArgoCD/Flux)** configurations.

---

## 🗺️ System Architecture

The platform is divided into a **Control Plane** for orchestration and a **Runner Cluster** for CPU-pinned, isolated execution.

```mermaid
flowchart TB
    subgraph Control Plane
        Dashboard[Operator Dashboard\nReact/FastAPI]
        Leaderboard[(Redis Leaderboard)]
        Scoring[Scoring Engine]
        Telemetry[Telemetry & Analytics]
        Governance[Federation & IaC Orchestration]
    end

    subgraph Runner Cluster [Isolated Runner Node]
        BotFleet[Distributed Bot Fleet\n100k+ TPS]
        Sequencer[Sequencer\nMonotonic Timestamps]
        
        Gateway[IPC Gateway\nZero-Jitter]
        
        Sandbox[Firecracker Sandbox\nContestant Engine]
        Reference[Reference Engine\nGolden Standard]
        
        Validator[Validation Ingester\nState & Replay Diffs]
    end

    BotFleet -->|Raw Orders (Kafka/gRPC)| Sequencer
    Sequencer -->|Sequenced Journal| Gateway
    Sequencer -->|Sequenced Journal| Reference
    
    Gateway -->|Shared Memory Ring Buffer| Sandbox
    
    Sandbox -->|Execution Reports| Validator
    Reference -->|Execution Reports| Validator
    
    Validator -->|Correctness Diffs| Scoring
    Sandbox -.->|Latency Metrics| Telemetry
    
    Scoring --> Leaderboard
    Telemetry --> Dashboard
```

*Tech Stack: Python 3.11+, FastAPI, React 19, gRPC/Protobuf, Apache Kafka (KRaft), PostgreSQL (TimescaleDB), Redis, Kubernetes, Terraform, Prometheus/Grafana.*

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker 24+ & Docker Compose
- (Optional) `kubectl` and `kind` for local Kubernetes deployment

### ⚡ The Fast Track (Docker Compose)
Launch the entire platform prototype locally, including Postgres, Redis, Kafka (KRaft), and the React Dashboard.

```bash
git clone https://github.com/orbaps/exchange.git
cd exchange

# Install Python dependencies and generate gRPC stubs
pip install -r requirements.txt
make proto

# Boot the distributed cluster
docker-compose up -d
```
Access the operator dashboard at **[http://localhost:8080](http://localhost:8080)**.

### 🌐 Cloud Deployment (Kubernetes / IaC)
To deploy the platform via Infrastructure as Code (IaC) to a Kubernetes cluster:

```bash
# Spin up a local multi-node Kubernetes cluster using KIND
./scripts/kind-cluster.sh  # Or .\scripts\kind-cluster.ps1 on Windows

# Deploy the full Helm chart
make kind-deploy
```

*For production GKE/OKE deployment, navigate to `iac/terraform/environments/production` and run `terraform apply`.*

---

## 💻 Contestant SDK & Submission Format

Contestants do not write network servers. They write pure, high-performance algorithms. Submissions are compiled as shared libraries (`.so` / `.dll`) exposing a strict C ABI. The platform loads it dynamically and communicates via shared memory.

```c
// 1. Initialize data structures
EngineHandle* engine_init(const InstrumentDefinition* instruments, uint32_t count);

// 2. Process incoming sequenced events (New, Cancel, Replace)
// 3. Write ExecutionReports to the outbound ring buffer
void engine_on_message(
    EngineHandle* handle, 
    const JournalRecord* record, 
    RingBufferWriter* out
);

// 4. Clean up
void engine_destroy(EngineHandle* handle);
```

> 💡 **Reference Implementation:** Check out the [`examples/`](examples/) directory for a complete contestant template.

---

## 🧪 Testing, Validation & CI/CD

Our CI/CD pipeline enforces hardcore engineering excellence:
- **100% Determinism Validation:** Ensuring zero flakiness across runs.
- **Security Audits:** `pip-audit`, CodeQL, and container scanning.
- **Matrix Builds:** Compiling and testing all 7 microservices.

```bash
make test           # Run 24+ test suites with coverage
make lint           # Ruff linting
make fmt            # Auto-formatting
make mypy           # Static type analysis
```

---

<div align="center">
<br/>
<p>Distributed under the <strong>MIT License</strong>. See <code>LICENSE</code> for more information.</p>
<p><b>Built for the obsessed. Engineered for fairness.</b> 🏛️</p>
</div>
]]>
