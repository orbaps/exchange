# PHASE 7.0
# Distributed Competition & Federation Layer

## Objective

Transform IICPC from a single-node competition platform into a federated deterministic competition ecosystem capable of:

- Multi-node execution
- Remote benchmark workers
- Distributed evaluation
- Artifact replication
- Cross-node leaderboards
- Federated tournament replay
- Cryptographic verification
- Deterministic scheduling

while preserving:

- Determinism
- Replayability
- Auditability
- Local-first execution
- No Kubernetes
- No Redis
- No External Database
- No Cloud Requirement

---

# Architecture Overview

                ┌────────────────────┐
                │  Coordinator Node  │
                └─────────┬──────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼

   Worker Node      Judge Node      Analytics Node

          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼

                Federated Leaderboard

---

# New Package

federation/

---

# federation/models.py

NodeRole
NodeCapabilities
NodeInfo
FederationMember
FederationConfig
FederationHeartbeat
FederationSnapshot

---

## Node Roles

COORDINATOR
WORKER
JUDGE
ANALYTICS
OBSERVER

---

## NodeInfo

node_id
hostname
version
public_key
roles
capabilities
registered_at

---

# federation/registry.py

FederationRegistry

Responsibilities:

register_node()
remove_node()
heartbeat()
discover_nodes()
get_node()
list_nodes()
cleanup_expired_nodes()

Heartbeat timeout:

30 seconds

Default interval:

5 seconds

---

# federation/discovery.py

DiscoveryService

Responsibilities:

announce()
discover()
heartbeat()
validate()

Supports:

Local LAN discovery
Static peer lists
Manual federation bootstrap

---

# federation/network.py

FederationServer
FederationClient

Protocols:

REST
WebSocket

No message brokers.

No Redis.

No Kafka.

---

# federation/security.py

FederationKeyPair
FederationSignature
FederationVerifier

Algorithms:

RSA-2048
Ed25519

Every outbound message must contain:

node_id
timestamp
payload_hash
signature

Verification required before processing.

---

# federation/scheduler.py

DistributedScheduler

Scheduling Modes:

ROUND_ROBIN
LEAST_LOADED
CAPABILITY_MATCH
RANDOM_SEEDED

Functions:

assign_work()
rebalance()
cancel()
retry()

Determinism Requirement:

All randomized scheduling uses:

tournament_seed

Identical seed:

identical assignments

---

# federation/jobs.py

DistributedJob
JobStatus
JobAssignment
JobResult

States:

PENDING
ASSIGNED
RUNNING
COMPLETED
FAILED
CANCELLED
RETRYING

---

# federation/evaluation.py

FederatedEvaluationRunner

Workflow:

Benchmark Suite
        ↓
Partition
        ↓
Dispatch
        ↓
Remote Evaluation
        ↓
Result Collection
        ↓
Judge Aggregation
        ↓
Profile Generation

Must preserve:

JudgeResult
JudgeExplanation
EvidenceItem

without modification.

---

# federation/artifacts.py

ArtifactReplicator

Functions:

push()
pull()
sync()
verify()
repair()

Replicated Assets:

Submissions
Snapshots
Tournament Journals
Evaluation Journals
Reports
Replay Timelines
Skill Profiles

Verification:

SHA256 mandatory

---

# federation/leaderboard.py

FederatedLeaderboard

Functions:

merge_snapshots()
resolve_conflicts()
rank()

Conflict Resolution:

1. Timestamp
2. Snapshot Hash
3. Node ID

---

# federation/replay.py

FederatedReplay

Functions:

merge_journals()
verify_order()
reconstruct_state()

Ordering:

timestamp
node_id

Output:

Single deterministic timeline

---

# federation/analytics.py

New Analytics Events

NODE_REGISTERED

NODE_REMOVED

NODE_HEARTBEAT

JOB_ASSIGNED

JOB_COMPLETED

JOB_FAILED

ARTIFACT_REPLICATED

FEDERATION_SYNC_COMPLETED

---

# Dashboard Integration

## Federation Overview

/federation

Displays:

Connected Nodes
Capabilities
Health
Version
Load
Heartbeat

---

## Jobs

/federation/jobs

Displays:

Assignments
Failures
Retries
Queue Depth

---

## Artifact Replication

/federation/artifacts

Displays:

Replication Status
Integrity Verification
Pending Sync

---

## Federation Replay

/federation/replay

Displays:

Merged Journal Timeline
Cross-Node Events
State Reconstruction

---

# API Endpoints

## Public

GET /api/public/federation/nodes

GET /api/public/federation/jobs

GET /api/public/federation/health

GET /api/public/federation/replay

GET /api/public/federation/leaderboard

---

## Admin

POST /api/admin/federation/register

POST /api/admin/federation/remove

POST /api/admin/federation/rebalance

POST /api/admin/federation/sync

POST /api/admin/federation/repair

---

# State Cache Extensions

_nodes

_jobs

_federation_health

_replication_status

_federation_replay

_federated_leaderboard

---

# Journaling

FederationJournal

Hash-Chained Ledger

record_node_join()
record_node_leave()
record_assignment()
record_completion()
record_replication()

Tamper Detection Mandatory

---

# Replay Requirements

Replay must reconstruct:

Node Registrations

Job Assignments

Leaderboard Evolution

Replication Events

Tournament Outcomes

Exactly.

---

# Testing Requirements

Minimum:

100+ Tests

Registry Tests
Scheduler Tests
Security Tests
Replication Tests
Replay Tests
Evaluation Tests
Leaderboard Merge Tests
Dashboard API Tests

---

# Success Criteria

Phase 7.0 is complete when:

✓ Multiple nodes join federation

✓ Remote execution works

✓ Scheduling is deterministic

✓ Artifacts replicate correctly

✓ Replay reconstructs federated timelines

✓ Security signatures verify correctly

✓ Distributed leaderboards merge properly

✓ Dashboard displays federation state

✓ Entire test suite passes

Expected Size:

8,000–12,000 LOC

100–150 Tests