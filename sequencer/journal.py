from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import Any, List, Dict

# --- Journal Envelope & Records ---
# Dataclasses and classes to handle storage and retrieval of sequenced events.

@dataclass
class JournalHeader:
    """Represents the metadata header at the start of a journal file."""
    magic: str
    version: int
    run_id: str
    created_at: int


@dataclass
class JournalRecord:
    """Represents a single entry envelope in the append-only journal file."""
    record_id: int
    sequence_id: int
    timestamp_ns: int
    event_type: str
    instrument: str
    payload: dict
    checksum: str
    
    def to_json(self) -> str:
        """Serializes the record to a JSON string."""
        return json.dumps(asdict(self))
        
    @staticmethod
    def from_json(data: str) -> JournalRecord:
        """Deserializes a JSON string into a JournalRecord."""
        d = json.loads(data)
        return JournalRecord(
            record_id=d['record_id'],
            sequence_id=d['sequence_id'],
            timestamp_ns=d['timestamp_ns'],
            event_type=d['event_type'],
            instrument=d['instrument'],
            payload=d['payload'],
            checksum=d['checksum']
        )
        
    def verify_checksum(self) -> bool:
        """Verifies if the stored checksum matches the payload."""
        expected = hashlib.sha256(json.dumps(self.payload, sort_keys=True).encode('utf-8')).hexdigest()
        return self.checksum == expected


class JournalWriter:
    """Manages appending sequenced records to an on-disk journal file using JSON lines."""

    def __init__(self, file_path: str) -> None:
        """Initializes the JournalWriter."""
        self.file_path = file_path
        self._file = None
        self._next_record_id = 1
        self._next_sequence_id = 1

    def open(self, path: str = None) -> None:
        """Opens the journal file for append-only writing."""
        p = path or self.file_path
        self._file = open(p, 'a', encoding='utf-8')

    def append(self, timestamp_ns: int, event_type: str, instrument: str, payload: dict) -> JournalRecord:
        """Appends a JournalRecord to the journal file."""
        if not self._file:
            self.open()
            
        checksum = hashlib.sha256(json.dumps(payload, sort_keys=True).encode('utf-8')).hexdigest()
        
        record = JournalRecord(
            record_id=self._next_record_id,
            sequence_id=self._next_sequence_id,
            timestamp_ns=timestamp_ns,
            event_type=event_type,
            instrument=instrument,
            payload=payload,
            checksum=checksum
        )
        
        self._file.write(record.to_json() + '\n')
        
        self._next_record_id += 1
        self._next_sequence_id += 1
        return record

    def flush(self) -> None:
        """Forces flushing of written bytes to physical disk storage."""
        if self._file:
            self._file.flush()

    def sync(self) -> None:
        import os
        self.flush()
        if self._file:
            os.fsync(self._file.fileno())

    def close(self) -> None:
        """Closes the active journal file descriptor."""
        if self._file:
            self._file.close()
            self._file = None


class JournalReader:
    """Manages reading and seeking through an on-disk JSON-lines journal file."""

    def __init__(self, file_path: str) -> None:
        """Initializes the JournalReader."""
        self.file_path = file_path
        self._file = None

    def open(self, path: str = None) -> None:
        """Opens the journal file for reading."""
        p = path or self.file_path
        self._file = open(p, 'r', encoding='utf-8')

    def next(self) -> JournalRecord:
        """Reads and returns the next JournalRecord."""
        if not self._file:
            raise RuntimeError("File not opened")
        line = self._file.readline()
        if not line:
            return None
        return JournalRecord.from_json(line)

    def read_all(self) -> List[JournalRecord]:
        """Reads all records from the journal."""
        records = []
        if not self._file:
            self.open()
        
        # Start from beginning
        self._file.seek(0)
        for line in self._file:
            if line.strip():
                records.append(JournalRecord.from_json(line))
        return records
        
    def read_range(self, start_seq: int, end_seq: int) -> List[JournalRecord]:
        """Reads a range of records by sequence_id (inclusive)."""
        all_records = self.read_all()
        return [r for r in all_records if start_seq <= r.sequence_id <= end_seq]

    def close(self) -> None:
        """Closes the journal file descriptor."""
        if self._file:
            self._file.close()
            self._file = None
