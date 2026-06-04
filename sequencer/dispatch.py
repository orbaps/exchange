from __future__ import annotations

from abc import ABC, abstractmethod
from sequencer.journal import JournalRecord

# --- Dispatcher & Consumers ---
# This module defines the interface and implementations for fanning out sequenced events.

class Consumer(ABC):
    """Abstract base class for all sequenced event consumers."""

    @abstractmethod
    def deliver(self, record: JournalRecord) -> None:
        """Delivers a JournalRecord to the target destination.

        Args:
            record: The JournalRecord to be delivered.
        """
        raise NotImplementedError


class Dispatcher:
    """Manages fan-out delivery of sequenced JournalRecords to registered consumers."""

    def __init__(self) -> None:
        """Initializes the Dispatcher with an empty list of consumers."""
        raise NotImplementedError

    def add_consumer(self, consumer: Consumer) -> None:
        """Registers a consumer for event delivery.

        Args:
            consumer: The Consumer to add.
        """
        raise NotImplementedError

    def dispatch(self, record: JournalRecord) -> None:
        """Broadcasts a JournalRecord to all registered consumers.

        Args:
            record: The JournalRecord to dispatch.
        """
        raise NotImplementedError


class IpcConsumer(Consumer):
    """Consumer that writes sequenced records to a shared-memory ring buffer (IPC)."""

    def __init__(self, shm_name: str, capacity: int, message_size: int) -> None:
        """Initializes the IpcConsumer.

        Args:
            shm_name: Name of the shared memory region.
            capacity: Buffer capacity.
            message_size: Size of individual message slots.
        """
        raise NotImplementedError

    def deliver(self, record: JournalRecord) -> None:
        """Encodes and writes the record to the shared-memory SPSC ring buffer.

        Args:
            record: The JournalRecord to deliver.
        """
        raise NotImplementedError


class KafkaConsumer(Consumer):
    """Consumer that publishes sequenced records to a designated Kafka topic for telemetry."""

    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        """Initializes the KafkaConsumer.

        Args:
            bootstrap_servers: The Kafka brokers connection string.
            topic: The destination topic.
        """
        raise NotImplementedError

    def deliver(self, record: JournalRecord) -> None:
        """Publishes the JournalRecord to the Kafka topic.

        Args:
            record: The JournalRecord to deliver.
        """
        raise NotImplementedError
