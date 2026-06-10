import sys
import json
import os
import traceback
import argparse
from typing import Dict, Any

# Ensure project root is in PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from submission.loader import SubmissionLoader
from submission.metadata import SubmissionMetadata
from validation_engine.snapshots import EngineSnapshot

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission-path", required=True)
    parser.add_argument("--events-path", required=True)
    parser.add_argument("--output-path", required=True)
    args = parser.parse_args()

    success = False
    error_msg = None
    
    snapshot_file = os.path.join(args.output_path, "snapshot.json")
    execution_file = os.path.join(args.output_path, "execution.json")

    try:
        # Load Metadata
        metadata_path = os.path.join(args.submission_path, "metadata.json")
        with open(metadata_path, "r") as f:
            metadata_dict = json.load(f)
            
        metadata = SubmissionMetadata(
            team_name=metadata_dict.get("team_name", "Unknown"),
            engine_class=metadata_dict["engine_class"],
            version=metadata_dict.get("version", "1.0")
        )

        # Load Engine
        load_result = SubmissionLoader.load(args.submission_path, metadata)
        if not load_result.success:
            raise RuntimeError(f"Failed to load engine: {load_result.errors}")
            
        engine = load_result.engine

        # Process Events
        import time
        with open(args.events_path, "r") as f:
            events_data = json.load(f)
            
        start_time = time.perf_counter()
        event_count = 0
        
        for event in events_data:
            event_type = event["event_type"]
            payload = event["payload"]
            
            if event_type == "NewOrderRequest":
                engine.submit_order(payload)
            elif event_type == "CancelOrderRequest":
                engine.cancel_order(payload)
            elif event_type == "ReplaceOrderRequest":
                engine.replace_order(payload)
            else:
                raise ValueError(f"Unknown event type: {event_type}")
            event_count += 1

        # Snapshot
        snapshot: EngineSnapshot = engine.snapshot()
        runtime_ms = (time.perf_counter() - start_time) * 1000.0
        
        from validation_engine.serialization import to_dict
        snapshot_dict = to_dict(snapshot)
        with open(snapshot_file, "w") as f:
            json.dump(snapshot_dict, f)
            
        success = True
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        
    finally:
        # Write WorkerResponse execution.json
        resp = {
            "success": success,
            "snapshot_path": snapshot_file if success else None,
            "error": error_msg,
            "runtime_ms": runtime_ms if 'runtime_ms' in locals() else 0.0,
            "event_count": event_count if 'event_count' in locals() else 0
        }
        with open(execution_file, "w") as f:
            json.dump(resp, f)
            
        if not success:
            sys.exit(1)
        sys.exit(0)

if __name__ == "__main__":
    main()
