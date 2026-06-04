# Phase 2.6 Implementation Plan

*Note: This implementation plan reflects the exact file changes and architectural decisions made to fulfill Phase 2.6, as the phase is already complete in the current repository.*

## 1. Exact Files to Modify

- `sequencer/journal.py`: Complete overhaul required to remove the binary skeleton and introduce JSON-line serialization and hash verification.

## 2. Exact Classes to Modify

- `JournalWriter` (in `sequencer/journal.py`): Modified to open a `.jsonl` file, accept dictionaries, convert them to JSON, compute SHA-256 hashes, and append lines.
- `JournalReader` (in `sequencer/journal.py`): Modified to parse `.jsonl` files and rehydrate `JournalRecord` classes.
- `JournalRecord` (in `sequencer/journal.py`): Re-structured to contain standard text-based fields (`record_id`, `event_type`, `instrument`, `payload`, `checksum`).

## 3. New Classes Required

### Replay Engine Architecture
- **`ReplayEngine`** (in `reference_engine/replay/engine.py`): Central processor to read a list of `JournalRecord`s and feed them sequentially into a clean `MatchingEngine`.
- **`ReplayResult`** (in `reference_engine/replay/engine.py`): A dataclass encapsulating the deep state of the matching engine at the end of a replay.

### Validation Engine Architecture
- **`BookSnapshot`, `OrderSnapshot`, `TradeSnapshot`, `EngineSnapshot`** (in `validation_engine/snapshots.py`): Immutable frozen dataclasses representing exact point-in-time state.
- **`ValidationRecord`** (in `validation_engine/ground_truth.py`): Encapsulates an `event_id` and the expected states of the engine.
- **`GroundTruthGenerator`** (in `validation_engine/ground_truth.py`): Hooks into the `EventBus` to emit snapshots dynamically.
- **`ReplayVerifier`** (in `validation_engine/replay_verifier.py`): Performs nested loop iterations to compare `ReplayResult` against `ValidationRecord` streams.
- **`ReplayVerificationResult`** (in `validation_engine/replay_verifier.py`): Simple wrapper containing a boolean and a list of structural error strings.

## 4. New Tests Required

- **Golden Scenario Suite** (`tests/golden/test_golden_scenarios.py`): Must contain explicitly constructed edge-case validations matching real-world trade behavior:
  - Scenario 1: Simple Fill
  - Scenario 2: Partial Fill
  - Scenario 3: FIFO Queue Management
  - Scenario 4: Multi-Level Fill (Sweeping the Book)
  - Scenario 5: Cancel After Partial Fill
- **Determinism Suite** (`tests/determinism/test_determinism.py`): Must contain a looping randomized script using a fixed PRNG seed to verify bit-level output identicality over 100 iterations.

## 5. Estimated Implementation Order

1. **Foundation (Journal)**: Build out the JSON JournalWriter and JournalReader.
2. **Replay Framework**: Construct the `ReplayEngine` logic for ingesting the journal back into the `MatchingEngine`.
3. **State Snapshots**: Build the immutable snapshot definitions to support deep engine introspection.
4. **Observation layer**: Create the `GroundTruthGenerator` hooked into the `EventBus`.
5. **Verification layer**: Connect the output of the Replay Engine and the Ground Truth Generator into the `ReplayVerifier`.
6. **Testing Validation**: Run the Golden Scenarios against the pipeline to fix typing issues or missing attributes.
7. **Determinism Stress Testing**: Run the 100-loop determinism suite to guarantee system reliability.
8. **Documentation**: Finalize markdown explanations of the Replay, Journal, and Validation architecture.
