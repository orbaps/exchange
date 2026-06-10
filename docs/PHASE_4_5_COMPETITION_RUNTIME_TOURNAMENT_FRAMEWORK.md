Objective

Build a framework capable of running:

Single Contest
Multi-Round Competition
Qualification Events
Elimination Brackets
Finals

using the existing infrastructure:

Hosting
Bot Fleet
Benchmarking
Scoring
Leaderboard
Analytics
Architecture
Tournament
      ↓

Stage

      ↓

Campaign

      ↓

Benchmark

      ↓

Score

      ↓

Leaderboard

      ↓

Advancement
Core Design Principles
Deterministic
Replayable
Auditable
Versioned
Fair
Module Layout
tournament/
├── __init__.py

├── models.py
├── stages.py
├── rules.py

├── runner.py
├── advancement.py

├── ranking.py

├── schedule.py

├── registry.py

├── snapshot.py

├── journal.py
├── replay.py

├── analytics.py

├── report.py
Task 1 — Tournament Models
tournament/models.py
TournamentStatus
DRAFT
SCHEDULED
RUNNING
COMPLETED
CANCELLED
Tournament
tournament_id
name
description

status

created_at
start_time
end_time

stages
TournamentResult
tournament_id

winner

final_rankings

stage_results
Task 2 — Tournament Registry
tournament/registry.py

Purpose:

Store all tournaments.

Functions:

create()

get()

list()

delete()

update()

Also:

latest()
Task 3 — Tournament Stages
tournament/stages.py
StageType
QUALIFICATION

GROUP_STAGE

SEMIFINAL

FINAL
TournamentStage

Fields:

stage_id

name

stage_type

campaign

advancement_rule

Purpose:

Each stage executes an existing BenchmarkCampaign.

Task 4 — Advancement Rules
tournament/advancement.py
AdvancementType
TOP_N

TOP_PERCENT

MIN_SCORE

CUSTOM
AdvancementRule

Fields:

rule_type

value

Examples:

TOP_N(10)

TOP_PERCENT(20)

MIN_SCORE(75)

Functions:

advance()

Input:

LeaderboardSnapshot

Output:

Qualified Contestants
Task 5 — Tournament Ranking
tournament/ranking.py
TournamentRanking

Purpose:

Merge:

multiple stages

into:

overall rankings

Tie-breaks:

Final Score
Correctness
Reliability
Latency
Submission ID

Reuse existing ranking engine.

Task 6 — Tournament Scheduler
tournament/schedule.py
TournamentSchedule

Fields:

start_time

registration_deadline

stage_times

Functions:

is_open()

is_running()

is_closed()

Purpose:

Competition lifecycle.

Task 7 — Tournament Runner
tournament/runner.py

Most important component.

TournamentRunner

Responsibilities:

Run Stages

Apply Advancement

Update Rankings

Generate Snapshots

Publish Analytics

Flow:

Qualification
      ↓

Top 20

      ↓

Semi Final

      ↓

Top 5

      ↓

Final

      ↓

Winner
Task 8 — Tournament Snapshots
tournament/snapshot.py
TournamentSnapshot

Immutable state capture.

Fields:

timestamp

stage

leaderboard

qualified

eliminated

Purpose:

Replay.

Task 9 — Tournament Journal
tournament/journal.py
TournamentJournal

Persist:

Stage Start
Stage End

Advancement

Elimination

Winner Declaration

Use:

JSONL
SHA256

same style as:

HostingJournal
AnalyticsJournal
ExecutionJournal
Task 10 — Tournament Replay
tournament/replay.py
TournamentReplay

Purpose:

Replay an entire competition.

Input:

TournamentJournal

Output:

TournamentTimeline

This becomes one of the most valuable debugging tools.

Task 11 — Tournament Analytics
tournament/analytics.py
TournamentAnalytics

Metrics:

active_contestants

eliminated_contestants

average_score

best_score

worst_score

stage_completion_rate

Purpose:

Competition monitoring.

Task 12 — Tournament Reports
tournament/report.py

Generate:

# Tournament Results

Winner:
Team Alpha

Runner Up:
Team Beta

Third:
Team Gamma

Qualification:
50 → 20

Semi Final:
20 → 5

Final:
5 → 1
Task 13 — Leaderboard Integration

Modify:

leaderboard/

Add:

tournament_id
stage_id

to snapshots.

Leaderboard becomes:

Tournament A
Qualification

Tournament A
Semi Final

Tournament A
Final

aware.

Task 14 — Analytics Integration

Modify:

analytics/

Publish:

TOURNAMENT_STARTED

STAGE_STARTED

ADVANCEMENT

ELIMINATION

WINNER_DECLARED

events.

Task 15 — Tests

Create:

tests/tournament/

Required:

test_advancement.py

Verify:

TOP_N
TOP_PERCENT
MIN_SCORE
test_runner.py

Verify:

Qualification
→ Semi
→ Final

progression.

test_snapshot.py

Verify:

Snapshot immutability
test_journal.py

Verify:

Replay consistency
test_end_to_end_tournament.py

Full test:

Register 20 contestants

↓

Deploy

↓

Run Qualification

↓

Advance Top 10

↓

Run Semi Final

↓

Advance Top 3

↓

Run Final

↓

Declare Winner

↓

Generate Report
Critical Enhancement

Add:

tournament/submission_lock.py
Submission Lock

Purpose:

Prevent contestants from changing submissions mid-tournament.

Functions:

lock_submission()

unlock_submission()

This mirrors real competitions.

Critical Enhancement

Add:

tournament/version_freeze.py

When tournament starts:

Team A → v7

gets frozen.

Even if:

Team A uploads v8

the tournament still uses:

v7

This is essential.