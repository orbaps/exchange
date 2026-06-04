# Phase 3.1 — Contestant Submission Framework

Version: 1.0

Status: Implementation Specification

Purpose:

Allow external contestant exchange implementations to be loaded and benchmarked by the platform.

This phase introduces:

* Submission Discovery
* Submission Validation
* Submission Loading
* Submission Packaging
* Engine Registration

This phase does NOT include:

* Docker
* Containers
* Kubernetes
* Cloud Deployment
* Web UI
* File Upload APIs
* Security Isolation

The objective is to create the minimal framework required to benchmark contestant implementations locally.

---

# Objective

Transform:

Contestant Code

into:

ContestantEngine

which can be executed by the Benchmark Runner.

---

# Architecture

Contestant Submission
│
▼

Submission Loader
│
▼

Contestant Adapter
│
▼

Benchmark Runner
│
▼

Validation Engine

---

# Submission Structure

Each contestant submission must follow:

contestant_submission/

├── metadata.json
├── engine.py
└── README.md

---

# metadata.json

Required:

{
"team_name": "Example Team",
"engine_class": "ContestantMatchingEngine",
"version": "1.0"
}

---

# engine.py

Must expose:

class ContestantMatchingEngine:
...

The engine must implement:

submit_order()

cancel_order()

replace_order()

snapshot()

reset()

---

# Task 1 — Submission Metadata

Create:

submission/metadata.py

Implement:

SubmissionMetadata

Fields:

* team_name
* version
* engine_class

Validation:

* required fields present
* non-empty strings

---

# Task 2 — Submission Validator

Create:

submission/validator.py

Implement:

SubmissionValidator

Responsibilities:

* validate folder structure
* validate metadata.json
* validate engine.py existence
* validate required class exists

Output:

ValidationResult

Pass or Fail.

---

# Task 3 — Submission Loader

Create:

submission/loader.py

Implement:

SubmissionLoader

Responsibilities:

* load metadata
* dynamically import engine.py
* instantiate engine class

Output:

ContestantEngine instance

---

# Task 4 — Submission Registry

Create:

submission/registry.py

Implement:

SubmissionRegistry

Stores:

* submission_id
* team_name
* version
* load_time

Capabilities:

register()

get()

list()

---

# Task 5 — Contestant Wrapper

Create:

submission/wrapper.py

Implement:

ContestantSubmissionAdapter

Purpose:

Convert arbitrary contestant engine into the ContestantEngine interface.

Responsibilities:

* normalize outputs
* normalize snapshots
* normalize exceptions

---

# Task 6 — Submission Result

Create:

submission/result.py

Implement:

SubmissionLoadResult

Fields:

* success
* metadata
* errors

---

# Task 7 — Example Submission

Create:

examples/contestant_submission/

Contains:

metadata.json

engine.py

README.md

The example should successfully benchmark against the existing framework.

---

# Task 8 — Tests

Create:

tests/submission/

Required Tests:

1. Valid Submission

2. Missing Metadata

3. Missing Engine File

4. Missing Engine Class

5. Invalid Metadata

6. Successful Dynamic Load

7. Successful Registry Entry

---

# Deliverables

Required:

* SubmissionMetadata
* SubmissionValidator
* SubmissionLoader
* SubmissionRegistry
* ContestantSubmissionAdapter
* SubmissionLoadResult
* Example Submission
* Submission Tests

---

# Success Criteria

The phase is complete when:

1. A contestant folder can be loaded.
2. The engine can be instantiated.
3. The engine can be wrapped.
4. The engine can run through BenchmarkRunner.
5. Validation passes.
6. Tests pass.

---

# Explicit Non-Goals

Do NOT implement:

* Docker
* Containers
* Kubernetes
* Sandboxing
* Security Isolation
* Upload APIs
* Web Interface
* Authentication
* Distributed Systems

Those belong to later phases.

This phase only prepares contestant code for benchmarking.
