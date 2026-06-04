# Phase 2.6 — Competition Reference Exchange Completion

Version: 1.0

Status: Implementation Specification

Purpose:
Transform the existing exchange core into a deterministic, replayable,
benchmark-grade reference engine capable of generating ground truth
for future contestant validation.

---

# Background

Current implementation already contains:

- Order Models
- Trade Models
- Multi-Instrument Support
- Matching Engine
- FIFO Matching
- Order Lifecycle
- Event Types
- Validation Engine Skeleton
- Journal Skeleton
- SDK Skeleton
- Sandbox Skeleton

The next goal is NOT to add more exchange features.

The next goal is:

```text
Convert the exchange into a benchmarking reference engine.
```

This phase focuses on:

1. Deterministic Replay
2. Ground Truth Generation
3. Validation Snapshots
4. Journal Completion
5. Replay Verification

No networking.
No distributed systems.
No Kubernetes.
No Kafka.
No database.

---

# Primary Goal

Given:

```text
Input Events
```

the engine must always produce:

```text
Same Trades
Same Order States
Same Order Book
Same Validation Records
```

regardless of:

- machine
- restart
- execution order

This becomes the foundation of correctness benchmarking.

---

# Architecture Overview

```text
                     Exchange Core

                            │
                            ▼

                    Matching Engine
                            │
                            ▼

                     Event Stream
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼

        Journal        Replay Engine   Validation

            ▼               ▼               ▼

     Ground Truth     State Recovery   Snapshots
```

---

# Task 1 — Complete Journal System

## Existing Components

Located in:

```text
sequencer/journal.py
```

Current classes:

```python
JournalWriter
JournalReader
JournalRecord
```

These exist but are incomplete.

---

## Objective

Persist every exchange event in deterministic order.

---

## JournalRecord

Required fields:

```python
record_id: int
sequence_id: int
timestamp_ns: int
event_type: str
instrument: str
payload: dict
checksum: str
```

---

## Requirements

### Record Ordering

Records must be strictly ordered.

Example:

```text
1
2
3
4
5
```

Never:

```text
1
3
2
4
```

---

### Integrity

Each record must include:

```text
SHA256 checksum
```

for corruption detection.

---

### Serialization

Support:

```python
to_json()
from_json()
```

---

### Journal Writer

Implement:

```python
append(record)
flush()
```

---

### Journal Reader

Implement:

```python
read_all()
read_range()
```

---

# Task 2 — Deterministic Replay Engine

Create:

```text
reference_engine/replay/
```

---

## ReplayEngine

Purpose:

```text
Reconstruct exchange state
from journal records.
```

---

### Input

```python
List[JournalRecord]
```

---

### Output

```python
ReplayResult
```

Containing:

```python
orders
trades
orderbooks
events
```

---

## Requirements

Replay must regenerate:

### Order State

```text
NEW
ACCEPTED
PARTIALLY_FILLED
FILLED
CANCELLED
```

---

### Trade History

All trades must be reconstructed.

---

### Order Book State

All price levels reconstructed.

---

### Event Stream

Replay must regenerate events in exact order.

---

# Task 3 — Validation Snapshots

Create:

```text
validation/snapshots.py
```

---

## BookSnapshot

Represents:

```text
Expected Order Book State
```

---

Fields:

```python
instrument
best_bid
best_ask
spread
bid_depth
ask_depth
timestamp
```

---

## OrderSnapshot

Represents:

```text
Expected Order State
```

---

Fields:

```python
order_id
status
remaining_quantity
filled_quantity
```

---

## TradeSnapshot

Represents:

```text
Expected Trade State
```

---

Fields:

```python
trade_id
price
quantity
```

---

## EngineSnapshot

Contains:

```python
book_snapshots
order_snapshots
trade_snapshots
```

---

# Task 4 — Ground Truth Generator

Create:

```text
validation/ground_truth.py
```

---

## GroundTruthGenerator

Purpose:

Generate canonical expected state.

---

### Input

Exchange events.

---

### Output

ValidationRecord.

---

## ValidationRecord

Fields:

```python
event_id
expected_book_state
expected_order_state
expected_trade_state
```

---

Purpose:

Future contestant engines will be compared against these records.

---

# Task 5 — Validation Checkpoints

Introduce checkpoints.

---

Example:

```text
Order Accepted
```

Generate:

```text
Snapshot
```

---

Example:

```text
Trade Executed
```

Generate:

```text
Snapshot
```

---

Example:

```text
Order Cancelled
```

Generate:

```text
Snapshot
```

---

Requirements:

Every state-changing operation must create:

```text
ValidationRecord
```

---

# Task 6 — Replay Verification Framework

Create:

```text
validation/replay_verifier.py
```

---

Purpose:

Verify replay correctness.

---

## Verification Process

Step 1

Run exchange.

---

Step 2

Generate journal.

---

Step 3

Replay journal.

---

Step 4

Compare:

```text
Orders
Trades
Books
Snapshots
```

---

Result:

```python
ReplayVerificationResult
```

---

# Task 7 — Golden Scenario Tests

Create:

```text
tests/golden/
```

---

## Scenario 1

Simple Fill

```text
BUY 100 @ 50
SELL 100 @ 50
```

---

Expected:

```text
Trade Generated
Book Empty
```

---

## Scenario 2

Partial Fill

```text
BUY 100 @ 50
SELL 20 @ 50
```

---

Expected:

```text
Trade 20
Remaining 80
```

---

## Scenario 3

FIFO

```text
BUY1 100 @ 50
BUY2 100 @ 50
SELL 150 @ 50
```

---

Expected:

```text
BUY1 filled
BUY2 partial
```

---

## Scenario 4

Multi-Level Match

```text
SELL 20 @ 50
SELL 30 @ 51
SELL 40 @ 52

BUY 70 @ 52
```

---

Expected:

```text
20 @ 50
30 @ 51
20 @ 52
```

---

## Scenario 5

Cancel After Partial Fill

```text
BUY 100
SELL 40
Cancel BUY
```

---

Expected:

```text
40 filled
60 cancelled
```

---

# Task 8 — Determinism Tests

Create:

```text
tests/determinism/
```

---

Requirement:

Run same scenario:

```text
100 times
```

---

Verify:

```text
Same Trades
Same Snapshots
Same Journal
Same Final State
```

---

# Task 9 — Performance Requirements

This phase is NOT performance-focused.

Correctness first.

Targets:

```text
10k orders
```

without correctness issues.

No optimization required.

---

# Task 10 — Documentation

Generate:

```text
docs/replay.md
docs/journal.md
docs/validation.md
```

Include:

### Replay Flow

### Snapshot Generation

### Validation Pipeline

### Ground Truth Generation

### Sequence Diagrams

---

# Deliverables

Required output:

```text
Completed Journal System
Replay Engine
Snapshot Models
Ground Truth Generator
Replay Verifier
Golden Tests
Determinism Tests
Documentation
```

---

# Success Criteria

The implementation is complete when:

1. Journal records all state changes.
2. Replay reconstructs identical state.
3. Snapshots are generated automatically.
4. Validation records exist for all state transitions.
5. Golden tests pass.
6. Determinism tests pass.
7. Replay verification passes.

---

# Explicit Non-Goals

Do NOT implement:

- Kafka
- Redis
- Docker
- Kubernetes
- REST APIs
- WebSockets
- FIX
- Databases
- Authentication
- Distributed Systems
- Bot Fleet

Those belong to future phases.

This phase is exclusively focused on turning the exchange core into a deterministic reference engine suitable for benchmarking contestant systems.