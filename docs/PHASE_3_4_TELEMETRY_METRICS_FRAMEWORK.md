# Phase 3.4 — Telemetry & Metrics Framework

Version: 1.0

Status: Implementation Specification

Purpose:

Capture, aggregate, and analyze benchmark execution metrics.

This phase introduces:

- Latency Measurements
- TPS Measurements
- Failure Metrics
- Percentile Calculations
- Metrics Aggregation

This phase does NOT include:

- Leaderboards
- Web UI
- Kafka
- Redis
- Prometheus
- Grafana
- Distributed Telemetry

Focus only on local telemetry collection.

---

# Objective

Transform:

Benchmark Execution

into

Quantifiable Performance Metrics

---

# Architecture

Benchmark Execution
        │
        ▼

Telemetry Collector

        ▼

Metric Samples

        ▼

Metric Aggregator

        ▼

Telemetry Report

---

# Required Metrics

## Latency

Capture:

- p50
- p90
- p95
- p99
- min
- max
- average

Units:

milliseconds

---

## Throughput

Capture:

TPS

Formula:

total_events / total_runtime_seconds

---

## Failure Metrics

Capture:

success_count

failure_count

timeout_count

crash_count

success_rate

failure_rate

---

## Correctness

Reuse:

ValidationResult.correctness_score

Do not reimplement correctness.

---

# Task 1 — Metric Sample

Create:

telemetry/sample.py

---

## MetricSample

Fields:

timestamp_ns

event_name

duration_ns

success

metadata

Purpose:

Raw telemetry point.

---

# Task 2 — Telemetry Collector

Create:

telemetry/collector.py

---

## TelemetryCollector

Responsibilities:

record()

clear()

samples()

count()

Stores:

MetricSample

in memory.

---

# Task 3 — Latency Calculator

Create:

telemetry/latency.py

---

## LatencyStatistics

Fields:

min_ms
max_ms
avg_ms

p50_ms
p90_ms
p95_ms
p99_ms

sample_count

---

## LatencyCalculator

Input:

List[MetricSample]

Output:

LatencyStatistics

---

# Task 4 — TPS Calculator

Create:

telemetry/tps.py

---

## TPSStatistics

Fields:

total_events

runtime_seconds

tps

---

# Task 5 — Failure Statistics

Create:

telemetry/failures.py

---

## FailureStatistics

Fields:

success_count

failure_count

timeout_count

crash_count

success_rate

failure_rate

---

# Task 6 — Telemetry Report

Create:

telemetry/report.py

---

## TelemetryReport

Aggregates:

LatencyStatistics

TPSStatistics

FailureStatistics

Correctness

Output:

Human-readable markdown

Example:

Latency:

p50: 1.2 ms
p90: 2.1 ms
p99: 4.3 ms

TPS:

12000

Success Rate:

99.7%

Correctness:

100%

---

# Task 7 — Benchmark Integration

Update:

benchmarking/runner.py

---

BenchmarkRunner must collect:

start_time

end_time

event_count

execution durations

and emit:

TelemetryReport

inside:

BenchmarkResult

---

# Task 8 — Campaign Integration

Update:

campaign/result.py

CampaignReport

---

Aggregate telemetry across:

all scenarios

all contestants

---

Compute:

average_latency

average_tps

average_success_rate

---

# Task 9 — Telemetry Tests

Create:

tests/telemetry/

Required Tests:

Latency Percentiles

TPS Calculation

Failure Calculation

Empty Sample Handling

Benchmark Integration

Campaign Aggregation

---

# Deliverables

MetricSample

TelemetryCollector

LatencyStatistics

TPSStatistics

FailureStatistics

TelemetryReport

Telemetry Tests

Benchmark Integration

Campaign Integration

---

# Success Criteria

The phase is complete when:

1. Latencies are collected.
2. TPS is computed.
3. Failures are tracked.
4. Percentiles are calculated.
5. BenchmarkResult contains telemetry.
6. Campaign results aggregate telemetry.
7. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

- Kafka
- Redis
- Prometheus
- Grafana
- OpenTelemetry
- Leaderboards
- Dashboards
- WebSockets

Those belong to future phases.

This phase is purely local telemetry collection.