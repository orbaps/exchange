# Phase 4.2 — Distributed Benchmark Workers & Engine Load Execution

Version: 1.0

Status: Implementation Specification

Purpose:

Execute generated trading traffic against contestant engines using isolated benchmark workers.

This phase introduces:

- Benchmark Workers
- Worker Pools
- Engine Execution Sessions
- Traffic Dispatch
- Load Execution Metrics

This phase does NOT include:

- Kubernetes
- Cloud Deployment
- Kafka
- Redis
- Frontend
- WebSockets

Focus only on distributed execution architecture within a single deployment.

---

# Objective

Transform:

Generated Trading Events

into

Real Engine Load

---

# Challenge Alignment

Original Requirement:

Thousands of bots bombard contestant endpoints.

Phase 4.1:
Generated traffic.

Phase 4.2:
Executes traffic.

---

# Architecture

Bot Campaign
      │
      ▼

Dispatch Queue

      ▼

Worker Pool

      ▼

Execution Session

      ▼

Contestant Engine

      ▼

Telemetry

      ▼

Scoring

---

# Design Principles

1. Isolation First
2. Reproducibility
3. Horizontal Worker Scaling
4. Fault Tolerance
5. Deterministic Scheduling

---

# Task 1 — Execution Events

Create:

execution/events.py

---

## ExecutionEvent

Fields:

event_id

worker_id

session_id

dispatch_timestamp_ns

completion_timestamp_ns

success

error

trading_event

---

Purpose:

Track actual execution.

---

# Task 2 — Execution Session

Create:

execution/session.py

---

## ExecutionSession

Represents:

One contestant engine under test.

Fields:

session_id

submission_id

engine

sandbox_config

---

Methods:

start()

stop()

reset()

execute(event)

---

Purpose:

Abstract contestant execution.

---

# Task 3 — Worker

Create:

execution/worker.py

---

## BenchmarkWorker

Responsibilities:

Receive TradingEvents.

Execute against ExecutionSession.

Emit ExecutionEvents.

Collect local metrics.

---

Methods:

run()

submit()

shutdown()

---

# Task 4 — Worker Pool

Create:

execution/pool.py

---

## WorkerPool

Responsibilities:

Create workers.

Assign sessions.

Distribute load.

Aggregate results.

---

Config:

worker_count

max_queue_size

---

# Task 5 — Dispatch Queue

Create:

execution/queue.py

---

## DispatchQueue

Thread-safe queue.

Purpose:

Buffer TradingEvents.

Support:

enqueue()

dequeue()

size()

---

Implementation:

queue.Queue

Only.

No Kafka.

---

# Task 6 — Event Dispatcher

Create:

execution/dispatcher.py

---

## EventDispatcher

Responsibilities:

Take BotCampaignResult.

Distribute TradingEvents.

Balance load across workers.

Preserve determinism.

---

Scheduling Rule:

Round Robin.

---

# Task 7 — Execution Metrics

Create:

execution/metrics.py

---

## ExecutionStatistics

Fields:

total_events

successful_events

failed_events

events_per_second

average_execution_time_ms

p50_ms

p90_ms

p99_ms

---

Purpose:

Measure real execution.

---

# Task 8 — Campaign Result Extension

Update:

campaign/result.py

---

Add:

execution_statistics

load_profile

event_count

worker_count

---

Purpose:

Expose execution performance.

---

# Task 9 — Telemetry Integration

Update:

telemetry/

---

Add:

ExecutionStatistics

to

TelemetryReport.

---

# Task 10 — Scoring Integration

Update:

scoring/

---

Allow scoring to consume:

real execution metrics

instead of synthetic generation metrics.

---

# Task 11 — Leaderboard Integration

Update:

leaderboard/

---

Expose:

worker_count

event_count

execution_tps

inside leaderboard metadata.

---

# Task 12 — Failure Handling

Required Cases:

Contestant Crash

Timeout

Worker Failure

Queue Overflow

Malformed Event

---

Failures must:

1. Be isolated.
2. Not stop campaign execution.
3. Be recorded in metrics.

---

# Task 13 — Tests

Create:

tests/execution/

Required Tests:

ExecutionSession

BenchmarkWorker

WorkerPool

DispatchQueue

Round Robin Scheduling

Crash Isolation

Timeout Isolation

Deterministic Execution

Metrics Aggregation

---

# Deliverables

ExecutionEvent

ExecutionSession

BenchmarkWorker

WorkerPool

DispatchQueue

EventDispatcher

ExecutionStatistics

Execution Tests

Telemetry Integration

Leaderboard Integration

---

# Success Criteria

The phase is complete when:

1. Bot events execute against contestant engines.
2. Multiple workers operate concurrently.
3. Failures are isolated.
4. Metrics are collected.
5. Campaigns continue after worker failures.
6. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

- Kubernetes
- Kafka
- Redis
- Cloud Workers
- REST APIs
- WebSockets

Those belong to later phases.

This phase focuses only on local distributed execution.