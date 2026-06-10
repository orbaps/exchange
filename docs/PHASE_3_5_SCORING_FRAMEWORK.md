# Phase 3.5 — Scoring Framework

Version: 1.0

Status: Implementation Specification

Purpose:

Convert:

- Correctness
- Latency
- Throughput
- Reliability

into a single ranking score.

This phase creates the official scoring model that will later drive the leaderboard.

This phase does NOT include:

- Leaderboard UI
- Frontend
- WebSockets
- Real-time Streaming
- Databases
- Distributed Systems

Focus only on score computation.

---

# Objective

Transform:

Validation Results
+
Telemetry Results

into:

Score

---

# Design Principles

1. Correctness First
2. Deterministic Scoring
3. Transparent Formula
4. Reproducible Results
5. No Hidden Weights

---

# Core Philosophy

A fast but incorrect exchange is useless.

Therefore:

Correctness dominates.

Example:

Correctness = 60%

Latency = Excellent

TPS = Excellent

Final Score should still be poor.

---

# Score Components

## Correctness Score

Source:

ValidationResult.correctness_score

Range:

0 – 100

Weight:

70%

---

## Latency Score

Source:

TelemetryReport.latency

Primary Metric:

p99 latency

Secondary Metric:

p95 latency

Range:

0 – 100

Weight:

15%

---

## Throughput Score

Source:

TelemetryReport.execution_statistics

Metric:

events_per_second

Range:

0 – 100

Weight:

10%

---

## Reliability Score

Source:

FailureStatistics

Metric:

success_rate

Range:

0 – 100

Weight:

5%

---

# Final Formula

final_score =

(
0.70 * correctness_score
+
0.15 * latency_score
+
0.10 * throughput_score
+
0.05 * reliability_score
)

Range:

0 – 100

---

# Task 1 — Score Models

Create:

scoring/models.py

---

## ScoreBreakdown

Fields:

correctness_score

latency_score

throughput_score

reliability_score

final_score

---

## ScoreResult

Fields:

contestant_id

scenario_id

breakdown

---

# Task 2 — Latency Scoring

Create:

scoring/latency.py

---

## LatencyScorer

Input:

LatencyStatistics

Output:

0 – 100

Reference Curve:

p99 <= 1 ms
→ 100

p99 <= 5 ms
→ 90

p99 <= 10 ms
→ 80

p99 <= 20 ms
→ 60

p99 <= 50 ms
→ 40

p99 > 50 ms
→ 20

Implement interpolation between bands.

---

# Task 3 — Throughput Scoring

Create:

scoring/throughput.py

---

## ThroughputScorer

Input:

ExecutionStatistics

Output:

0 – 100

Reference Curve:

EPS >= 100000
→ 100

EPS >= 50000
→ 90

EPS >= 25000
→ 80

EPS >= 10000
→ 60

EPS >= 5000
→ 40

EPS < 5000
→ 20

---

# Task 4 — Reliability Scoring

Create:

scoring/reliability.py

---

## ReliabilityScorer

Input:

FailureStatistics

Output:

0 – 100

Formula:

success_rate

Example:

99.7% success
→ 99.7 score

---

# Task 5 — Score Calculator

Create:

scoring/calculator.py

---

## ScoreCalculator

Responsibilities:

1. Read telemetry
2. Read validation
3. Calculate component scores
4. Produce final score

Output:

ScoreResult

---

# Task 6 — Campaign Integration

Update:

campaign/result.py

campaign/report.py

---

Each contestant should have:

average_score

best_score

worst_score

---

Campaign reports should display:

Correctness

Latency

TPS

Reliability

Final Score

---

# Task 7 — Scoring Report

Create:

scoring/report.py

---

## ScoreReport

Markdown output.

Example:

Contestant: Team Alpha

Correctness: 100.0

Latency: 92.3

Throughput: 87.1

Reliability: 100.0

Final Score: 96.1

---

# Task 8 — Scoring Tests

Create:

tests/scoring/

Required Tests:

Perfect Correctness

Poor Correctness

Excellent Latency

Poor Latency

Excellent Throughput

Poor Throughput

Reliability Degradation

Final Formula Validation

Campaign Integration

---

# Deliverables

ScoreBreakdown

ScoreResult

LatencyScorer

ThroughputScorer

ReliabilityScorer

ScoreCalculator

ScoreReport

Scoring Tests

Campaign Integration

---

# Success Criteria

The phase is complete when:

1. Scores are deterministic.
2. Component scores are visible.
3. Final score is reproducible.
4. Campaigns aggregate scores.
5. Reports display scores.
6. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

- Leaderboards
- Databases
- APIs
- WebSockets
- Ranking Services
- Real-time Updates

Those belong to Phase 4.

This phase only computes scores.