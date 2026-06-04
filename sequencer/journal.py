from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# --- Journal Envelope & Records ---
# Dataclasses and classes to handle storage and retrieval of sequenced events.

@dataclass
class JournalHeader:
    """Represents the metadata header at the start of a journal file."""
    magic: bytes
    version: int
    run_id: str
    created_at: int


@dataclass
class JournalRecord:
    """Represents a single entry envelope in the append-only journal file."""
    global_sequence_no: int
    logical_timestamp: int
    wall_clock_ns: int
    run_id: str
    payload: bytes


class JournalWriter:
    """Manages appending sequenced records to an on-disk binary journal file."""

    def __init__(self, file_path: str) -> None:
        """Initializes the JournalWriter.

        Args:
            file_path: The file path to write the journal.
        """
        raise NotImplementedError

    def open(self, path: str) -> None:
        """Opens the journal file for append-only writing.

        Args:
            path: Path to the journal file.
        """
        raise NotImplementedError

    def append(self, record: JournalRecord) -> None:
        """Appends a JournalRecord to the journal file using a length-prefixed format.

        Args:
            record: The JournalRecord to write.
        """
        raise NotImplementedError

    def sync(self) -> None:
        """Forces flushing of written bytes to physical disk storage (fsync)."""
        raise NotImplementedError

    def close(self) -> None:
        """Closes the active journal file descriptor."""
        raise NotImplementedError


class JournalReader:
    """Manages reading and seeking through an on-disk binary journal file."""

    def __init__(self, file_path: str) -> None:
        """Initializes the JournalReader.

        Args:
            file_path: The file path to read from.
        """
        raise NotImplementedError

    def open(self, path: str) -> None:
        """Opens the journal file for reading.

        Args:
            path: Path to the journal file.
        """
        raise NotImplementedError

    def next(self) -> JournalRecord:
        """Reads and returns the next JournalRecord from the current offset.

        Returns:
            JournalRecord: The next record.
        """
        raise NotImplementedError

    def seek(self, sequence_no: int) -> None:
        """Positions the reader index at the start of the record with the given sequence number.

        Args:
            sequence_no: The sequence number to seek to.
        """
        raise NotImplementedError

    def has_next(self) -> bool:
        """Checks if there are more records left to read.

        Returns:
            bool: True if more records exist, False otherwise.
        """
        raise NotImplementedError

    def close(self) -> None:
        """Closes the journal file descriptor."""
        raise NotImplementedError
