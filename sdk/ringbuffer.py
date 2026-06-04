from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from contracts.messages import ExecutionReport

# ---
# Shared Memory SPSC Ring Buffer Python Interfaces
# ---

class IRingBuffer(ABC):
    """Abstract interface representing a lock-free Single Producer Single Consumer ring buffer."""

    @abstractmethod
    def create(self, shm_name: str, capacity: int, message_size: int) -> None:
        """Creates or attaches to a shared-memory POSIX ring buffer."""
        raise NotImplementedError

    @abstractmethod
    def write(self, msg: bytes) -> bool:
        """Writes raw binary message payload to the buffer. Returns success status."""
        raise NotImplementedError

    @abstractmethod
    def read(self) -> bytes:
        """Reads the next available message from the ring buffer."""
        raise NotImplementedError

    @abstractmethod
    def is_empty(self) -> bool:
        """Checks if there are no unread slots in the buffer."""
        raise NotImplementedError

    @abstractmethod
    def is_full(self) -> bool:
        """Checks if the buffer is full and cannot accept new writes."""
        raise NotImplementedError


@dataclass
class RingBufferWriter:
    """Wraps writing ExecutionReports directly to the outbound ring buffer."""
    buffer_address: int

    def write(self, report: ExecutionReport) -> bool:
        """Encodes and writes an ExecutionReport to the wrapped buffer."""
        raise NotImplementedError
