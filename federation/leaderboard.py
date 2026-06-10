import hashlib
from typing import List, Any, Dict, Optional

class FederatedLeaderboard:
    """Manages merging and conflict resolution of leaderboards across federated nodes."""
    
    def merge_snapshots(self, snapshots: List[Any]) -> Optional[Any]:
        """
        Merges multiple LeaderboardSnapshots from different nodes.
        Resolves conflicts for the same contestant_id using:
          1. Timestamp (newer wins)
          2. Snapshot Hash (higher hash wins)
          3. Node ID (lexicographically smaller node_id wins)
        """
        if not snapshots:
            return None

        # contestant_id -> (entry, snapshot_associated)
        merged_entries: Dict[str, Any] = {}

        for snap in snapshots:
            entries = getattr(snap, "entries", None) or snap.get("entries", [])
            for entry in entries:
                contestant_id = getattr(entry, "contestant_id", None) or entry.get("contestant_id")
                if not contestant_id:
                    continue

                if contestant_id not in merged_entries:
                    merged_entries[contestant_id] = (entry, snap)
                else:
                    existing_entry, existing_snap = merged_entries[contestant_id]
                    # Determine winner
                    winner = self._resolve_conflict(entry, snap, existing_entry, existing_snap)
                    if winner == "new":
                        merged_entries[contestant_id] = (entry, snap)

        # Rank all merged entries
        ranked_entries = self.rank([item[0] for item in merged_entries.values()])

        # Build merged snapshot
        first_snap = snapshots[0]
        # We can construct a dict or dynamic object matching LeaderboardSnapshot
        # Let's check if first_snap is dict or object
        is_dict = isinstance(first_snap, dict)
        
        # Calculate a deterministic snapshot_id for the merged result
        hash_input = "".join(sorted(merged_entries.keys()))
        merged_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:12]
        
        merged_data = {
            "snapshot_id": f"merged_{merged_hash}",
            "campaign_id": getattr(first_snap, "campaign_id", None) or first_snap.get("campaign_id", "merged_campaign"),
            "timestamp": str(max([float(getattr(s, "timestamp", 0.0) or s.get("timestamp", 0.0)) for s in snapshots])),
            "entries": ranked_entries,
            "entry_count": len(ranked_entries),
            "generated_at": "Federated Merger",
            "load_profile": "FEDERATED",
            "event_count": sum([int(getattr(s, "event_count", 0) or s.get("event_count", 0)) for s in snapshots]),
            "campaign_size": len(ranked_entries),
            "worker_count": len(snapshots),
            "execution_tps": sum([float(getattr(s, "execution_tps", 0.0) or s.get("execution_tps", 0.0)) for s in snapshots])
        }
        
        if not is_dict:
            # Reconstruct as LeaderboardSnapshotResponse if possible
            try:
                from dashboard.models.schemas import LeaderboardSnapshotResponse, LeaderboardEntryResponse
                entry_objs = []
                for e in ranked_entries:
                    entry_objs.append(LeaderboardEntryResponse(**e))
                merged_data["entries"] = entry_objs
                return LeaderboardSnapshotResponse(**merged_data)
            except Exception:
                pass
                
        return merged_data

    def _resolve_conflict(self, new_entry: Any, new_snap: Any, old_entry: Any, old_snap: Any) -> str:
        """Compares new and old entries and returns 'new' if new wins, else 'old'."""
        # 1. Compare Timestamp
        new_ts = float(getattr(new_snap, "timestamp", None) or new_snap.get("timestamp", 0.0))
        old_ts = float(getattr(old_snap, "timestamp", None) or old_snap.get("timestamp", 0.0))
        if new_ts != old_ts:
            return "new" if new_ts > old_ts else "old"

        # 2. Compare Snapshot Hash (represented by snapshot_id)
        new_id = getattr(new_snap, "snapshot_id", None) or new_snap.get("snapshot_id", "")
        old_id = getattr(old_snap, "snapshot_id", None) or old_snap.get("snapshot_id", "")
        new_hash = hashlib.sha256(new_id.encode("utf-8")).hexdigest()
        old_hash = hashlib.sha256(old_id.encode("utf-8")).hexdigest()
        if new_hash != old_hash:
            return "new" if new_hash > old_hash else "old"

        # 3. Compare Node ID
        new_node = getattr(new_snap, "tournament_id", None) or new_snap.get("tournament_id", "z_node")
        old_node = getattr(old_snap, "tournament_id", None) or old_snap.get("tournament_id", "z_node")
        return "new" if new_node < old_node else "old"

    def rank(self, entries: List[Any]) -> List[Dict[str, Any]]:
        """Sorts entries by score (descending) and assigns sequential ranks."""
        # Convert all to dicts for uniform sorting/return
        dict_entries = []
        for e in entries:
            if hasattr(e, "__dict__"):
                dict_entries.append(dict(e.__dict__))
            else:
                dict_entries.append(dict(e))

        # Sort: score descending, then contestant_id ascending (tie-breaker)
        sorted_list = sorted(
            dict_entries,
            key=lambda item: (-item.get("score", 0.0), item.get("contestant_id", ""))
        )

        # Re-assign rank
        for idx, entry in enumerate(sorted_list):
            entry["rank"] = idx + 1

        return sorted_list
