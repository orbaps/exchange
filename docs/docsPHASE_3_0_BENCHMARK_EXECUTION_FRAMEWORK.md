# Phase 3.0 — Benchmark Execution Framework

Version: 1.0

Status: Implementation Specification

Purpose:

Execute identical benchmark scenarios against:

1. Reference Exchange Engine
2. Contestant Exchange Engine

Capture results.

Run validation.

Produce benchmark reports.

This phase does NOT include:

- Docker
- Kubernetes
- Distributed Workers
- Kafka
- Redis
- Frontend
- Leaderboard
- WebSockets
- REST APIs

Focus only on benchmark execution.

---

# Objective

Given:

Scenario
↓
Reference Engine

and

Scenario
↓
Contestant Engine

produce:

Benchmark Result

containing:

- Correctness
- Validation Failures
- Execution Metrics

---

# Architecture

```text
Benchmark Scenario
          │
          ▼

     Benchmark Runner
          │
    ┌─────┴─────┐
    ▼           ▼

Reference   Contestant
 Engine       Engine

    ▼           ▼

Snapshots   Snapshots

    └─────┬─────┘
          ▼

 Validation Engine
          ▼

 Benchmark Result
```

---

# Task 1 — Benchmark Scenario

Create:

```text
benchmarking/scenario.py
```

---

## BenchmarkScenario

Represents deterministic test input.

Fields:

```python
scenario_id
name
description
events
seed
```

---

## ScenarioEvent

Represents:

```python
place_order
cancel_order
replace_order
```

---

Fields:

```python
timestamp
event_type
payload
```

---

Requirement:

Events must be replayable.

---

# Task 2 — Contestant Adapter

Create:

```text
benchmarking/contestant_adapter.py
```

---

Purpose:

Normalize contestant implementations.

---

Interface:

```python
ContestantEngine
```

Required methods:

```python
submit_order()
cancel_order()
replace_order()

snapshot()

reset()
```

---

Goal:

Allow different contestant engines
to be benchmarked through one API.

---

# Task 3 — Reference Adapter

Create:

```text
benchmarking/reference_adapter.py
```

---

Wrap existing reference engine.

Expose same interface as:

```python
ContestantEngine
```

---

This ensures:

```text
Reference
and
Contestant
```

run identically.

---

# Task 4 — Benchmark Runner

Create:

```text
benchmarking/runner.py
```

---

## BenchmarkRunner

Responsibilities:

1. Load scenario
2. Execute reference engine
3. Execute contestant engine
4. Capture snapshots
5. Run validation
6. Produce benchmark result

---

Interface:

```python
run(
    scenario,
    contestant
)
```

Returns:

```python
BenchmarkResult
```

---

# Task 5 — Benchmark Result

Create:

```text
benchmarking/result.py
```

---

Fields:

```python
scenario_id

correctness_score

validation_result

execution_time_ms

snapshot_count

mismatch_count
```

---

# Task 6 — Metrics Collection

Create:

```text
benchmarking/metrics.py
```

---

Collect:

```python
start_time
end_time
execution_time
```

---

For now only:

```text
Execution Duration
```

No latency percentiles yet.

---

# Task 7 — Scenario Library

Create:

```text
benchmarking/scenarios/
```

Implement:

---

Simple Fill

```text
BUY 100 @ 50
SELL 100 @ 50
```

---

Partial Fill

```text
BUY 100 @ 50
SELL 20 @ 50
```

---

FIFO

```text
BUY1 100 @ 50
BUY2 100 @ 50
SELL 150 @ 50
```

---

Multi-Level Fill

```text
SELL 20 @ 50
SELL 30 @ 51
SELL 40 @ 52

BUY 70 @ 52
```

---

Cancel

```text
BUY 100
SELL 40
CANCEL BUY
```

---

# Task 8 — Benchmark Tests

Create:

```text
tests/benchmarking/
```

---

Verify:

Reference vs Reference

produces:

```text
100% correctness
```

---

Verify:

Modified contestant state

produces:

```text
<100% correctness
```

---

Verify:

BenchmarkResult
contains expected metrics.

---

# Deliverables

Required output:

- BenchmarkScenario
- ContestantAdapter
- ReferenceAdapter
- BenchmarkRunner
- BenchmarkResult
- Metrics Collector
- Scenario Library
- Benchmark Tests

---

# Success Criteria

The phase is complete when:

1. A scenario can execute against both engines.
2. Validation runs automatically.
3. Correctness score is produced.
4. BenchmarkResult is generated.
5. Tests pass.

At completion:

The project can benchmark exchange engines.

This becomes the foundation for future:

- Submission Pipeline
- Sandbox
- Bot Fleet
- Telemetry
- Leaderboard