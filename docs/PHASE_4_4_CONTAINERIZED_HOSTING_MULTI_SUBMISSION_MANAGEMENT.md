# Phase 4.4 — Containerized Hosting & Multi-Submission Management

Version: 1.0

Status: Implementation Specification

Purpose:

Transform contestant submissions into isolated deployable services that can be hosted, managed, benchmarked, and terminated safely.

This phase introduces:

- Container Lifecycle Management
- Submission Registry
- Deployment Manager
- Resource Isolation
- Endpoint Routing
- Multi-Submission Scheduling

This phase does NOT include:

- Kubernetes
- Cloud Deployment
- Service Mesh
- Kafka
- Redis

Focus only on local container orchestration.

---

# Objective

Transform:

Contestant Submission

into

Running Hosted Service

---

# Challenge Alignment

Original Requirement:

Contestants upload source code or binaries.

Platform hosts submission.

Bots interact with hosted endpoints.

This phase implements exactly that.

---

# Architecture

Submission Upload
        │
        ▼

Submission Registry

        ▼

Build Manager

        ▼

Container Manager

        ▼

Running Instance

        ▼

Endpoint Router

        ▼

Bot Fleet

---

# Design Principles

1. Isolation First
2. Resource Fairness
3. Deterministic Deployment
4. Multi-Tenant Safety
5. Reproducibility

---

# Task 1 — Submission Manifest

Create:

hosting/manifest.py

---

## SubmissionManifest

Fields:

submission_id

team_name

version

language

entrypoint

build_command

run_command

resource_profile

---

Purpose:

Standardize deployments.

---

# Task 2 — Submission Registry

Create:

hosting/registry.py

---

## SubmissionRegistry

Responsibilities:

register()

get()

list()

remove()

update()

---

Purpose:

Track all submissions.

---

# Task 3 — Build Manager

Create:

hosting/build.py

---

## BuildStatus

Enum:

PENDING

BUILDING

SUCCESS

FAILED

---

## BuildResult

Fields:

build_id

submission_id

status

duration_ms

logs

artifact_path

---

## BuildManager

Responsibilities:

Validate submission

Execute build process

Generate deployable artifact

Capture logs

---

Purpose:

Prepare contestant code for execution.

---

# Task 4 — Resource Profiles

Create:

hosting/resources.py

---

## ResourceProfile

Fields:

cpu_limit

memory_limit_mb

disk_limit_mb

execution_timeout_sec

---

Profiles:

SMALL

MEDIUM

LARGE

---

Purpose:

Fair benchmarking.

---

# Task 5 — Container Lifecycle

Create:

hosting/container.py

---

## ContainerState

Enum:

CREATED

STARTING

RUNNING

STOPPED

FAILED

TERMINATED

---

## ContainerInstance

Fields:

container_id

submission_id

state

endpoint

resource_profile

---

Methods:

start()

stop()

restart()

terminate()

health()

---

Purpose:

Represent hosted engine.

---

# Task 6 — Container Manager

Create:

hosting/manager.py

---

## ContainerManager

Responsibilities:

deploy()

stop()

restart()

destroy()

list_running()

health_check()

---

Purpose:

Control all hosted submissions.

---

# Task 7 — Endpoint Router

Create:

hosting/router.py

---

## RouteEntry

Fields:

submission_id

endpoint

container_id

---

## EndpointRouter

Responsibilities:

register()

resolve()

remove()

list()

---

Purpose:

Map submissions to endpoints.

---

# Task 8 — Multi-Submission Scheduling

Create:

hosting/scheduler.py

---

## DeploymentScheduler

Responsibilities:

Queue deployments

Limit concurrent deployments

Prevent resource exhaustion

---

Configuration:

max_active_containers

max_concurrent_builds

---

# Task 9 — Health Monitoring

Create:

hosting/health.py

---

## DeploymentHealth

Fields:

submission_id

container_id

status

uptime

restart_count

failure_count

---

Purpose:

Monitor hosted services.

---

# Task 10 — Integration

Update:

submission/
sandbox/
execution/
analytics/

---

ExecutionSession must be able to:

resolve endpoint
→ route request
→ hosted container

instead of direct adapter invocation.

---

# Task 11 — Hosting Telemetry

Create:

hosting/telemetry.py

---

## HostingStatistics

Fields:

active_containers

failed_containers

average_startup_time

deployment_success_rate

build_success_rate

---

Purpose:

Operational metrics.

---

# Task 12 — Hosting Journal

Create:

hosting/journal.py

---

## HostingJournal

Persist:

Build Events

Deployment Events

Health Events

Termination Events

Use:

JSONL
SHA256

---

Purpose:

Auditable hosting layer.

---

# Task 13 — Replay Support

Create:

hosting/replay.py

---

## HostingReplay

Replay:

builds
deployments
health transitions

Purpose:

Debug infrastructure behavior.

---

# Task 14 — Tests

Create:

tests/hosting/

Required Tests:

Submission Registry

Build Manager

Container Lifecycle

Endpoint Routing

Deployment Scheduler

Health Monitoring

Hosting Replay

Hosting Journal

Concurrent Deployments

Resource Profile Enforcement

---

# Deliverables

SubmissionManifest

BuildManager

ContainerManager

EndpointRouter

DeploymentScheduler

DeploymentHealth

HostingStatistics

HostingJournal

HostingReplay

Hosting Tests

---

# Success Criteria

The phase is complete when:

1. Submissions can be registered.
2. Builds can be executed.
3. Deployments can be started.
4. Multiple submissions run concurrently.
5. Routing resolves endpoints.
6. Health monitoring works.
7. Journaling works.
8. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

- Kubernetes
- Docker Swarm
- Service Mesh
- Kafka
- Redis
- Cloud Infrastructure

Those belong to Phase 5.

This phase focuses only on local hosting orchestration.