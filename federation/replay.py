from typing import List, Dict, Any, Optional

class FederatedReplay:
    """Combines and reconstructs system states from multi-node federated transaction logs."""
    
    @staticmethod
    def get_sort_key(entry: Dict[str, Any]) -> tuple:
        """Extracts deterministic sorting key based on timestamp and node_id."""
        payload = entry.get("payload", {})
        # Check standard fields first
        ts = payload.get("timestamp_ns") or payload.get("timestamp") or entry.get("timestamp_ns") or entry.get("timestamp") or 0
        node = payload.get("node_id") or entry.get("node_id") or payload.get("contestant_id") or ""
        return (float(ts), str(node))

    def merge_journals(self, journals: List[Any]) -> List[Dict[str, Any]]:
        """
        Reads all entries from the provided list of journals and merges them
        into a single sorted list ordered by timestamp, then node_id.
        """
        all_entries = []
        for journal in journals:
            # support both journal objects and lists of raw dicts
            entries = getattr(journal, "read_all", None)
            if entries:
                try:
                    raw_entries = journal.read_all()
                except Exception:
                    raw_entries = []
            else:
                raw_entries = journal if isinstance(journal, list) else []
                
            for entry in raw_entries:
                # normalize format
                if "entry" in entry:
                    all_entries.append(entry["entry"])
                else:
                    all_entries.append(entry)
                    
        # Sort deterministically
        return sorted(all_entries, key=self.get_sort_key)

    def verify_order(self, timeline_entries: List[Dict[str, Any]]) -> bool:
        """Verifies that timeline entries are strictly sorted chronologically."""
        if len(timeline_entries) <= 1:
            return True
            
        last_key = self.get_sort_key(timeline_entries[0])
        for entry in timeline_entries[1:]:
            current_key = self.get_sort_key(entry)
            if current_key < last_key:
                return False
            last_key = current_key
        return True

    def reconstruct_state(self, timeline_entries: List[Dict[str, Any]], index: int) -> Dict[str, Any]:
        """Reconstructs the global federation state up to the specified event index."""
        state = {
            "nodes": {},
            "jobs": {},
            "leaderboard": None,
            "replicated_count": 0,
            "winner": None,
            "sync_completed_count": 0
        }
        
        if index < 0 or index >= len(timeline_entries):
            return state

        for i in range(index + 1):
            entry = timeline_entries[i]
            event_type = entry.get("event_type") or entry.get("event_type")
            # Fallback if inside payload
            payload = entry.get("payload", {})
            
            if not event_type and "event_type" in entry:
                event_type = entry["event_type"]
                
            # Process events
            if event_type == "NODE_REGISTERED":
                node_id = payload.get("node_id")
                if node_id:
                    state["nodes"][node_id] = {
                        "node_id": node_id,
                        "hostname": payload.get("hostname"),
                        "roles": payload.get("roles", []),
                        "status": "ACTIVE"
                    }
                    
            elif event_type == "NODE_REMOVED":
                node_id = payload.get("node_id")
                if node_id in state["nodes"]:
                    state["nodes"][node_id]["status"] = "OFFLINE"
                    
            elif event_type == "NODE_HEARTBEAT":
                node_id = payload.get("node_id")
                if node_id in state["nodes"]:
                    state["nodes"][node_id]["load"] = payload.get("load", 0.0)
                    state["nodes"][node_id]["status"] = "ACTIVE"
                    
            elif event_type == "JOB_ASSIGNED":
                job_id = payload.get("job_id")
                if job_id:
                    state["jobs"][job_id] = {
                        "job_id": job_id,
                        "node_id": payload.get("node_id"),
                        "status": "ASSIGNED"
                    }
                    
            elif event_type == "JOB_COMPLETED":
                job_id = payload.get("job_id")
                if job_id in state["jobs"]:
                    state["jobs"][job_id]["status"] = "COMPLETED"
                    
            elif event_type == "JOB_FAILED":
                job_id = payload.get("job_id")
                if job_id in state["jobs"]:
                    state["jobs"][job_id]["status"] = "FAILED"
                    
            elif event_type == "ARTIFACT_REPLICATED":
                state["replicated_count"] += 1
                
            elif event_type == "FEDERATION_SYNC_COMPLETED":
                state["sync_completed_count"] += 1
                
            elif event_type in ("WINNER_DECLARED", "WINNER_DECLARATION"):
                state["winner"] = payload.get("winner")
                
            elif event_type == "LEADERBOARD_UPDATE":
                state["leaderboard"] = payload
                
        return state
