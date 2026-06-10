# Phase 4.0 — Leaderboard & Ranking Engine

Version: 1.0

Status: Implementation Specification

Purpose:

Provide a ranking system that converts campaign results and scoring outputs into a dynamic leaderboard.

This phase introduces:

- Ranking Engine
- Leaderboard Models
- Tie-Break Rules
- Historical Ranking Snapshots
- Ranking Reports

This phase does NOT include:

- React
- Frontend UI
- WebSockets
- REST APIs
- Databases
- Real-Time Streaming

Focus only on ranking logic.

---

# Objective

Transform:

Campaign Results

into

Leaderboard Rankings

---

# Challenge Alignment

Original challenge requirement:

Real-Time Leaderboard & Analytics

This phase implements:

Leaderboard

Analytics arrive later.

---

# Ranking Philosophy

Correctness dominates.

A contestant with:

100 correctness
90 latency
80 throughput

must always rank above:

60 correctness
100 latency
100 throughput

even if the latter is faster.

---

# Task 1 — Leaderboard Models

Create:

leaderboard/models.py

---

## LeaderboardEntry

Fields:

contestant_id

rank

score

average_correctness

average_latency

average_tps

success_rate

campaign_id

---

## LeaderboardSnapshot

Fields:

snapshot_id

campaign_id

timestamp

entries

---

# Task 2 — Ranking Engine

Create:

leaderboard/ranking.py

---

## RankingEngine

Input:

CampaignResult

Output:

LeaderboardSnapshot

---

Sorting Order:

1. Final Score (Descending)
2. Correctness (Descending)
3. Reliability (Descending)
4. Latency (Ascending)
5. Contestant ID (Ascending)

---

Purpose:

Guarantee deterministic rankings.

---

# Task 3 — Tie Breaker System

Create:

leaderboard/tiebreak.py

---

## TieBreaker

Responsibilities:

Resolve equal-score scenarios.

Rules:

Rule 1:
Higher Correctness Wins

Rule 2:
Higher Reliability Wins

Rule 3:
Lower Latency Wins

Rule 4:
Alphabetical Contestant ID

---

# Task 4 — Ranking History

Create:

leaderboard/history.py

---

## RankingHistory

Stores:

List[LeaderboardSnapshot]

Operations:

add_snapshot()

latest()

get_snapshot()

---

Purpose:

Enable future ranking progression analytics.

---

# Task 5 — Leaderboard Analytics

Create:

leaderboard/analytics.py

---

## LeaderboardAnalytics

Metrics:

best_score

worst_score

average_score

median_score

score_spread

---

Input:

LeaderboardSnapshot

---

Output:

AnalyticsReport

---

# Task 6 — Leaderboard Report

Create:

leaderboard/report.py

---

## LeaderboardReport

Generate:

Markdown

Example:

# Leaderboard

Rank  Contestant   Score

1     Team Alpha   96.1

2     Team Beta    93.4

3     Team Gamma   88.0

---

Also display:

Correctness
Latency
TPS
Success Rate

---

# Task 7 — Campaign Integration

Update:

campaign/report.py

---

Generate:

Leaderboard section

after campaign execution.

---

# Task 8 — Ranking Tests

Create:

tests/leaderboard/

Required Tests:

Ranking Order

Tie Break Rules

Historical Snapshot Storage

Analytics Computation

Deterministic Rankings

Report Generation

---

# Deliverables

LeaderboardEntry

LeaderboardSnapshot

RankingEngine

TieBreaker

RankingHistory

LeaderboardAnalytics

LeaderboardReport

Leaderboard Tests

Campaign Integration

---

# Success Criteria

The phase is complete when:

1. Contestants are ranked.
2. Rankings are deterministic.
3. Tie-breaks work.
4. Snapshots are stored.
5. Reports generate correctly.
6. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

- React
- HTML
- CSS
- APIs
- WebSockets
- Databases
- Redis
- Kafka

Those belong to future phases.

This phase is only about ranking logic.
One Important Change Beyond The Original Spec

I would additionally create:

leaderboard/rating.py
RatingGrade

Purpose:

Convert score into human-readable tiers.

Example:

95–100   S+
90–95    S
85–90    A+
80–85    A
70–80    B
60–70    C
<60      D

Leaderboard entry:

rating_grade

Why?

Judges often understand:

S Tier
A Tier

faster than:

91.73
89.42