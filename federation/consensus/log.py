import json
import hashlib
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from federation.clock import global_clock

def calculate_checksum(index: int, term: int, timestamp: int, command: Dict[str, Any]) -> str:
    """Deterministically calculate SHA256 checksum for a log entry."""
    serialized = json.dumps(command, sort_keys=True)
    payload = f"{index}:{term}:{timestamp}:{serialized}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

@dataclass
class LogEntry:
    index: int
    term: int
    timestamp: int
    command: Dict[str, Any]
    checksum: str
    committed: bool = False

    def verify(self) -> bool:
        """Verify the integrity checksum of the log entry."""
        return self.checksum == calculate_checksum(self.index, self.term, self.timestamp, self.command)

class ConsensusLog:
    """Manages the replicated sequence of log entries for state replication."""

    def __init__(self):
        self.entries: List[LogEntry] = []
        self.commit_index: int = 0

    def append(self, term: int, command: Dict[str, Any], timestamp: Optional[int] = None) -> LogEntry:
        """Create and append a new log entry."""
        idx = len(self.entries) + 1
        ts = timestamp if timestamp is not None else int(global_clock.now())
        chk = calculate_checksum(idx, term, ts, command)
        entry = LogEntry(
            index=idx,
            term=term,
            timestamp=ts,
            command=command,
            checksum=chk,
            committed=False
        )
        self.entries.append(entry)
        return entry

    def commit(self, index: int) -> None:
        """Mark log entries up to index as committed."""
        self.commit_index = max(self.commit_index, index)
        for entry in self.entries:
            if entry.index <= self.commit_index:
                entry.committed = True

    def truncate(self, index: int) -> None:
        """Truncate the log, removing entries after the given index."""
        # index is 1-based, list is 0-based
        if index < 0:
            index = 0
        self.entries = self.entries[:index]
        if self.commit_index > index:
            self.commit_index = index

    def replay(self, state_machine: Any) -> List[Any]:
        """Replay all committed log entries onto a state machine."""
        results = []
        for entry in self.entries:
            if entry.index <= self.commit_index:
                # Expect state_machine to have apply_command(command)
                res = state_machine.apply_command(entry.command)
                results.append(res)
        return results

    def verify_integrity(self) -> bool:
        """Verify checksum integrity across all entries in the log."""
        for entry in self.entries:
            if not entry.verify():
                return False
        return True
