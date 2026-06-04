# Phase 3.2 — Benchmark Campaign Framework

Version: 1.0

Status: Implementation Specification

Purpose:

Execute large collections of benchmark scenarios against multiple contestant submissions.

This phase introduces campaign management.

The framework should support:

* Multiple scenarios
* Multiple contestant submissions
* Batch execution
* Aggregate reporting

This phase does NOT include:

* Docker
* Containers
* Kubernetes
* Distributed Workers
* Kafka
* Redis
* Web UI
* Leaderboard

Focus only on campaign orchestration.

---

# Objective

Transform:

Many Scenarios

and

Many Contestants

into:

Campaign Results

---

# Architecture

Contestants
│

Scenarios
│

```
  ▼
```

Campaign Runner

```
  ▼
```

Benchmark Runner

```
  ▼
```

Campaign Results

---

# Task 1 — Campaign Definition

Create:

campaign/campaign.py

---

## BenchmarkCampaign

Fields:

campaign_id
name
description
scenarios
contestants

---

Requirements:

A campaign contains:

* N scenarios
* M contestants

---

# Task 2 — Campaign Result

Create:

campaign/result.py

---

## CampaignResult

Fields:

campaign_id

total_runs

successful_runs

failed_runs

results

---

## ContestantCampaignResult

Fields:

contestant_id

average_correctness

total_mismatches

scenario_results

---

# Task 3 — Campaign Runner

Create:

campaign/runner.py

---

## CampaignRunner

Responsibilities:

1. Load campaign
2. Execute all scenarios
3. Execute all contestants
4. Invoke BenchmarkRunner
5. Collect results

---

Execution Pattern:

for contestant:

```
for scenario:

    run benchmark
```

---

Output:

CampaignResult

---

# Task 4 — Campaign Metrics

Create:

campaign/metrics.py

---

Compute:

average_correctness

maximum_correctness

minimum_correctness

average_execution_time

---

No latency analysis yet.

---

# Task 5 — Campaign Report

Create:

campaign/report.py

---

## CampaignReport

Generate:

Human-readable summary.

Example:

Contestant A
Correctness: 100%

Contestant B
Correctness: 87%

---

Output:

Markdown report.

---

# Task 6 — Campaign Library

Create:

campaign/examples/

---

Provide:

small_campaign.py

Contains:

2 contestants

5 scenarios

---

# Task 7 — Failure Isolation

Campaign execution must continue.

Example:

Contestant A

Scenario 3

fails.

Campaign must continue.

Record:

Failure

Continue.

---

# Task 8 — Campaign Tests

Create:

tests/campaign/

---

Required Tests:

Campaign Creation

Campaign Execution

Multiple Contestants

Multiple Scenarios

Failure Isolation

Report Generation

Metrics Calculation

---

# Deliverables

Required:

BenchmarkCampaign

CampaignRunner

CampaignResult

ContestantCampaignResult

CampaignMetrics

CampaignReport

Campaign Tests

Example Campaign

---

# Success Criteria

The phase is complete when:

1. Multiple contestants can run.
2. Multiple scenarios can run.
3. Results are aggregated.
4. Failures are isolated.
5. Reports are generated.
6. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

* Docker
* Containers
* Sandboxing
* Bot Fleet
* Telemetry
* Kafka
* Redis
* Leaderboard
* Frontend

Those belong to future phases.

This phase is exclusively focused on benchmark campaign orchestration.
