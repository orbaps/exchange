import json
from typing import Dict, Any, List

from benchmarking.scenario import BenchmarkScenario, ScenarioEvent
from benchmarking.contestant_adapter import ContestantEngine
from submission.metadata import SubmissionManifest
from validation_engine.snapshots import EngineSnapshot

from sandbox.config import SandboxConfig
from sandbox.runner import SandboxRunner

class SandboxedContestantAdapter(ContestantEngine):
    """
    Phase 3.3:
    Buffered execution model.
    Events are accumulated and executed during snapshot().
    
    This adapter provides a ContestantEngine-compatible interface,
    but internally queues events and dispatches them to a sandbox
    subprocess in bulk.
    """
    
    def __init__(self, manifest: SubmissionManifest, config: SandboxConfig = None):
        self._manifest = manifest
        self._config = config or SandboxConfig()
        self._events: List[ScenarioEvent] = []
        self._seq = 1

    def _buffer(self, event_type: str, payload: Dict[str, Any]) -> None:
        self._events.append(
            ScenarioEvent(
                timestamp=payload.get("timestamp_ns", 0),
                event_type=event_type,
                payload=payload
            )
        )

    def submit_order(self, payload: Dict[str, Any]) -> None:
        self._buffer("NewOrderRequest", payload)

    def cancel_order(self, payload: Dict[str, Any]) -> None:
        self._buffer("CancelOrderRequest", payload)

    def replace_order(self, payload: Dict[str, Any]) -> None:
        self._buffer("ReplaceOrderRequest", payload)

    def snapshot(self) -> EngineSnapshot:
        # Create a temporary scenario from the buffered events
        scenario = BenchmarkScenario(
            scenario_id=f"buffered_{self._seq}",
            name="Buffered execution",
            description="",
            seed=0,
            events=self._events
        )
        self._seq += 1
        
        # Execute sandbox
        runner = SandboxRunner(self._config)
        
        # We need the temp_dir to persist slightly longer or read it back inside run_submission.
        # Wait, run_submission cleans up the temp_dir before returning. But it returns SandboxResult.
        # How do we get the snapshot? run_submission needs to parse snapshot.json and attach it to SandboxResult, or we just modify SandboxResult to hold the snapshot dict.
        # Wait, SandboxResult in spec does not have snapshot field, but we can add snapshot_data: dict.
        # Let me modify run_submission to read snapshot.json before tempdir cleanup, and add snapshot_data to SandboxResult.
        # Then the adapter parses snapshot_data into EngineSnapshot.
        
        # Actually, let's call SandboxRunner.run_worker directly to control the output directory.
        import tempfile, os
        from sandbox.protocol import WorkerRequest
        
        with tempfile.TemporaryDirectory() as temp_dir:
            events_path = os.path.join(temp_dir, "events.json")
            with open(events_path, "w") as f:
                json.dump([{"event_type": e.event_type, "payload": e.payload} for e in self._events], f)
                
            request = WorkerRequest(
                submission_path=self._manifest.submission_path,
                events_path=events_path,
                output_path=temp_dir
            )
            
            result = runner.run_worker(request)
            
            if not result.success:
                raise RuntimeError(f"Sandbox execution failed. Crashed: {result.crashed}, Timeout: {result.timed_out}, Error: {result.exception_message}\nStderr:\n{result.stderr}")
                
            snapshot_path = os.path.join(temp_dir, "snapshot.json")
            if not os.path.exists(snapshot_path):
                raise RuntimeError("Sandbox execution succeeded but snapshot.json was not produced.")
                
            with open(snapshot_path, "r") as f:
                snapshot_data = json.load(f)
                
        # Parse snapshot_data back to EngineSnapshot
        return self._parse_snapshot(snapshot_data)

    def _parse_snapshot(self, data: Dict[str, Any]) -> EngineSnapshot:
        from validation_engine.snapshots import BookSnapshot, OrderSnapshot, TradeSnapshot
        
        book_snapshots = {}
        for sym, bdata in data.get("book_snapshots", {}).items():
            book_snapshots[sym] = BookSnapshot(
                instrument=bdata["instrument"],
                best_bid=bdata["best_bid"],
                best_ask=bdata["best_ask"],
                spread=bdata["spread"],
                bid_depth=bdata["bid_depth"],
                ask_depth=bdata["ask_depth"],
                timestamp=bdata["timestamp"]
            )
            
        order_snapshots = {}
        for sym, sorders in data.get("order_snapshots", {}).items():
            order_snapshots[sym] = {}
            for oid, odata in sorders.items():
                order_snapshots[sym][int(oid)] = OrderSnapshot(
                    order_id=odata["order_id"],
                    status=odata["status"],
                    remaining_quantity=odata["remaining_quantity"],
                    filled_quantity=odata["filled_quantity"]
                )
                
        trade_snapshots = {}
        for sym, strades in data.get("trade_snapshots", {}).items():
            trade_snapshots[sym] = []
            for tdata in strades:
                trade_snapshots[sym].append(TradeSnapshot(
                    trade_id=tdata["trade_id"],
                    price=tdata["price"],
                    quantity=tdata["quantity"]
                ))
                
        return EngineSnapshot(
            book_snapshots=book_snapshots,
            order_snapshots=order_snapshots,
            trade_snapshots=trade_snapshots
        )

    def reset(self) -> None:
        self._events.clear()
