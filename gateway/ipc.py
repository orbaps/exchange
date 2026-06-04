from __future__ import annotations

from typing import Any

# --- IPC & Shared Memory Subsystem ---
# Manages POSIX shared memory allocations and SPSC lock-free ring buffers.

class SharedMemoryManager:
    """Manages POSIX shared memory segment lifecycle: creation, mapping, and deletion."""

    def __init__(self, name: str, size: int) -> None:
        """Initializes the SharedMemoryManager.

        Args:
            name: The POSIX shared memory segment name.
            size: The segment size in bytes.
        """
        raise NotImplementedError

    def create(self) -> None:
        """Creates the shared memory segment."""
        raise NotImplementedError

    def map(self) -> memoryview:
        """Maps the shared memory segment into the process space.

        Returns:
            memoryview: A memory view mapping of the shared memory.
        """
        raise NotImplementedError

    def unmap(self) -> None:
        """Unmaps the shared memory segment."""
        raise NotImplementedError

    def close(self) -> None:
        """Closes the shared memory file descriptor."""
        raise NotImplementedError

    def unlink(self) -> None:
        """Unlinks/deletes the POSIX shared memory name."""
        raise NotImplementedError


class RingBuffer:
    """A wait-free, single-producer single-consumer (SPSC) shared-memory ring buffer."""

    def __init__(self, capacity: int, message_size: int) -> None:
        """Initializes the RingBuffer structure.

        Args:
            capacity: The number of slots (must be a power of 2).
            message_size: The byte size of each slot.
        """
        raise NotImplementedError

    def attach(self, shm_name: str) -> None:
        """Attaches to an existing shared memory ring buffer.

        Args:
            shm_name: The shared memory region name.
        """
        raise NotImplementedError

    def write(self, msg: bytes) -> bool:
        """Writes a message to the ring buffer.

        Args:
            msg: The binary payload.

        Returns:
            bool: True if successful, False if buffer is full.
        """
        raise NotImplementedError

    def read(self) -> bytes | None:
        """Reads a message from the ring buffer.

        Returns:
            bytes | None: The binary payload, or None if empty.
        """
        raise NotImplementedError

    def is_empty(self) -> bool:
        """Checks if the buffer is empty.

        Returns:
            bool: True if empty.
        """
        raise NotImplementedError

    def is_full(self) -> bool:
        """Checks if the buffer is full.

        Returns:
            bool: True if full.
        """
        raise NotImplementedError


class RingBufferWriter:
    """Writer wrapper around RingBuffer for higher-level execution report serialization."""

    def __init__(self, buffer: RingBuffer) -> None:
        """Initializes the RingBufferWriter.

        Args:
            buffer: The underlying RingBuffer.
        """
        raise NotImplementedError

    def write(self, message: Any) -> bool:
        """Writes an object to the ring buffer after serializing it.

        Args:
            message: The message object.

        Returns:
            bool: True if write succeeded.
        """
        raise NotImplementedError


class RingBufferReader:
    """Reader wrapper around RingBuffer for polling inbound commands."""

    def __init__(self, buffer: RingBuffer) -> None:
        """Initializes the RingBufferReader.

        Args:
            buffer: The underlying RingBuffer.
        """
        raise NotImplementedError

    def read(self) -> bytes | None:
        """Polls and returns the raw bytes of the next message.

        Returns:
            bytes | None: The raw message bytes, or None.
        """
        raise NotImplementedError
