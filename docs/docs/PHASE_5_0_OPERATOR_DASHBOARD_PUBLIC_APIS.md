Goal

Expose every backend subsystem through:

REST APIs
WebSocket Streams
Admin Dashboard
Public Leaderboard
Replay Viewer

Current state:

Backend Complete

After Phase 5.0:

Competition Platform Complete
Architecture
                     Browser
                         │
                         ▼
                 Dashboard Frontend
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼

 Public API       Admin API       WebSocket API

       │                 │                 │

       └─────────────────┼─────────────────┘
                         ▼

                 Backend Services

     Tournament
     Leaderboard
     Hosting
     Analytics
     Benchmarking
Design Goals
Realtime
Observable
Operator Friendly
Replayable
Competition Ready
New Top-Level Modules
api/
├── public/
├── admin/
├── websocket/

dashboard/
├── backend/
├── frontend/

auth/
├── roles.py
├── permissions.py

replay_viewer/
Stream A — Public APIs

These are visible to contestants.

api/public
GET /leaderboard

Returns:

{
  "tournament":"alpha-cup",
  "stage":"semifinal",
  "entries":[]
}

Source:

LeaderboardSnapshot
GET /contestants

Returns:

{
  "contestants":[]
}
GET /tournaments

Returns:

{
  "tournaments":[]
}
GET /tournament/{id}

Returns:

{
  "status":"RUNNING",
  "stages":[]
}
GET /results/{contestant}

Returns:

{
  "scores":[]
}
Stream B — Admin APIs

These control the system.

api/admin
POST /tournament/start

Input:

{
  "tournament_id":"..."
}
POST /tournament/stop
POST /deployment/restart

Restart container.

POST /deployment/terminate

Kill submission.

POST /campaign/run

Manual benchmark execution.

GET /health

System status.

Returns:

{
  "containers":17,
  "healthy":16,
  "failed":1
}
Stream C — WebSocket Layer

Most important.

api/websocket

Real-time updates.

Channel
leaderboard

Publishes:

{
  "rank":1,
  "score":97.2
}
Channel
analytics

Publishes:

{
  "latency":2.1,
  "tps":14000
}
Channel
tournament

Publishes:

{
  "event":"ADVANCEMENT"
}
Channel
health

Publishes:

{
  "container":"abc",
  "status":"RUNNING"
}
Authentication Layer

New package:

auth/
roles.py
ADMIN
OPERATOR
JUDGE
CONTESTANT
VIEWER
permissions.py

Examples:

ADMIN:
  everything

CONTESTANT:
  leaderboard only

VIEWER:
  public only
Dashboard Backend

New package:

dashboard/backend
DashboardService

Aggregates:

Leaderboard
Analytics
Hosting
Tournament

Provides unified APIs.

Dashboard Frontend

Use:

React
TypeScript
Vite

Recommended.

Pages:

/

Overview.

/leaderboard

Live rankings.

/tournament

Tournament state.

/submissions

Contestants.

/deployments

Container health.

/analytics

Performance.

Leaderboard Page

Display:

Rank
Contestant
Score
Correctness
Latency
TPS
Reliability

Live updating.

Tournament Page

Display:

Qualification
Semi Final
Final

Show:

advanced
eliminated
remaining
Deployment Page

Display:

Container ID
Submission
Status
CPU
Memory
Restarts

Directly from hosting subsystem.

Analytics Page

Graphs:

Latency
TPS
Success Rate
Container Count

Use:

Recharts

or

Chart.js
Replay Viewer

New subsystem.

replay_viewer/

Uses:

TournamentReplay
AnalyticsReplay
HostingReplay

Operator can select:

Tournament

then:

Play
Pause
Step Forward
Step Back

through timeline.

This is a major differentiator in judging.

Dashboard State

Create:

dashboard/backend/state.py

Aggregate:

CurrentTournament
CurrentLeaderboard
CurrentAnalytics
CurrentHostingState

Single source of truth.

API Framework

Use:

FastAPI

Reason:

REST
WebSocket
OpenAPI
Pydantic

all built in.

Frontend Framework

Use:

React

with:

Vite

Reason:

Fast
Simple
Competition Ready
Testing

Create:

tests/api/
tests/dashboard/
tests/websocket/

Required Tests

API
leaderboard endpoint

tournament endpoint

health endpoint
WebSocket
broadcast

multiple subscribers

disconnect recovery
Dashboard
state refresh

leaderboard updates

analytics updates
Critical Requirement

Do NOT build:

microservices
kubernetes
cloud
postgres
redis

yet.

Keep:

single-process
modular
local-first

because judges care about:

working platform

not cloud complexity.