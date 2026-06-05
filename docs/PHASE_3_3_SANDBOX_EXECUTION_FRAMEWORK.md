# Phase 3.3 — Sandbox Execution Framework

Version: 1.0

Status: Implementation Specification

Purpose:

Execute contestant submissions in isolated processes.

This phase introduces:

- Process Isolation
- Crash Isolation
- Timeout Enforcement
- Resource Limiting
- Sandbox Result Collection

This phase does NOT include:

- Docker
- Containers
- Kubernetes
- Cloud Deployment
- Distributed Workers
- Kafka
- Redis
- Networking
- REST APIs
- WebSockets

The goal is to safely execute untrusted contestant code without allowing it to crash the benchmark platform.

---

# Objective

Transform:

Contestant Submission

into

Sandboxed Contestant Execution

while preserving compatibility with:

- Submission Framework
- Benchmark Runner
- Campaign Runner
- Validation Engine

---

# Architecture

Submission
     │
     ▼

Sandbox Manager
     │
     ▼

Sandbox Process
     │
     ▼

Contestant Engine

     │
     ▼

Sandbox Result

---

# Design Principles

1. Isolation First
2. Correctness Before Performance
3. Deterministic Behavior
4. Fail Closed
5. Simple Process Model

---

# Task 1 — Sandbox Configuration

Create:

sandbox/config.py

---

## SandboxConfig

Fields:

```python
timeout_seconds: int
memory_limit_mb: int
cpu_time_limit_seconds: int
capture_stdout: bool
capture_stderr: bool
```

Default:

```python
timeout_seconds = 10
memory_limit_mb = 512
cpu_time_limit_seconds = 10
capture_stdout = True
capture_stderr = True
```

---

# Task 2 — Sandbox Result

Create:

sandbox/result.py

---

## SandboxResult

Fields:

```python
success: bool

exit_code: int | None

runtime_ms: float

timed_out: bool

crashed: bool

stdout: str

stderr: str

exception_type: str | None

exception_message: str | None
```

---

# Task 3 — Sandbox Process

Create:

sandbox/process.py

---

## SandboxProcess

Responsibilities:

- start process
- stop process
- kill process
- collect result

Interface:

```python
start()

wait()

terminate()

kill()
```

Implementation:

```python
subprocess.Popen(...)
```

ONLY.

No containers.

---

# Task 4 — Resource Limiter

Create:

sandbox/limits.py

---

## ResourceLimiter

Purpose:

Apply:

- memory limits
- CPU time limits

Platform Support:

Unix/Linux first.

If platform unsupported:

Gracefully skip.

---

# Task 5 — Sandbox Runner

Create:

sandbox/runner.py

---

## SandboxRunner

Responsibilities:

1. Create sandbox process
2. Apply limits
3. Execute contestant
4. Capture output
5. Detect crashes
6. Detect timeout
7. Return SandboxResult

---

Interface:

```python
run_submission(
    submission_manifest,
    scenario
)
```

Returns:

```python
SandboxResult
```

---

# Task 6 — Sandbox Adapter

Create:

sandbox/adapter.py

---

## SandboxedContestantAdapter

Implements:

```python
ContestantEngine
```

Purpose:

Allow benchmark framework to communicate with a sandboxed contestant exactly as if it were local.

---

# Task 7 — Crash Detection

Must detect:

---

## Unhandled Exception

Example:

```python
raise RuntimeError(...)
```

---

## Process Exit

Example:

```python
sys.exit(1)
```

---

## Infinite Loop

Example:

```python
while True:
    pass
```

Must trigger:

```python
timed_out = True
```

---

## Fatal Error

Example:

Segmentation fault.

Must produce:

```python
crashed = True
```

---

# Task 8 — Sandbox Event Logging

Create:

sandbox/logging.py

---

## SandboxEvent

Fields:

```python
timestamp

submission_id

event_type

message
```

---

Supported Types:

```python
STARTED
FINISHED
CRASHED
TIMED_OUT
KILLED
```

---

# Task 9 — Sandbox Tests

Create:

tests/sandbox/

---

Required Tests:

### Normal Submission

Expected:

```python
success == True
```

---

### Exception Submission

Expected:

```python
crashed == True
```

---

### Timeout Submission

Expected:

```python
timed_out == True
```

---

### Exit Code Failure

Expected:

```python
success == False
```

---

### Stdout Capture

Expected:

Captured output.

---

### Stderr Capture

Expected:

Captured errors.

---

# Task 10 — Campaign Integration

Update:

campaign/runner.py

---

Requirements:

CampaignRunner must support:

```python
use_sandbox=True
```

When enabled:

```python
SandboxedContestantAdapter
```

is used automatically.

---

# Deliverables

Required:

SandboxConfig

SandboxResult

SandboxProcess

ResourceLimiter

SandboxRunner

SandboxedContestantAdapter

SandboxEvent

Sandbox Tests

Campaign Integration

---

# Success Criteria

The phase is complete when:

1. Contestant runs in separate process.
2. Crashes do not affect platform.
3. Timeouts are enforced.
4. Resource limits are applied.
5. Outputs are captured.
6. Campaigns continue after failures.
7. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

- Docker
- Containers
- Kubernetes
- Virtual Machines
- Networking
- REST APIs
- WebSockets
- Distributed Execution
- Cloud Deployment

Those belong to future phases.

This phase is only about safe local process isolation.