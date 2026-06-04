from __future__ import annotations

from typing import Any

# --- SBE Protocol Codecs ---
# Encoders and decoders for Simple Binary Encoding (SBE) serialization formats.

class SbeEncoder:
    """Encodes high-level domain objects into SBE (Simple Binary Encoding) flat binary format."""

    def __init__(self) -> None:
        """Initializes the SbeEncoder."""
        raise NotImplementedError

    def encode_journal_record(self, record: Any) -> bytes:
        """Encodes a JournalRecord envelope and its payload to binary.

        Args:
            record: The JournalRecord object.

        Returns:
            bytes: The SBE encoded bytes.
        """
        raise NotImplementedError

    def encode_execution_report(self, report: Any) -> bytes:
        """Encodes an ExecutionReport to binary.

        Args:
            report: The ExecutionReport object.

        Returns:
            bytes: The SBE encoded bytes.
        """
        raise NotImplementedError

    def encode_new_order_request(self, request: Any) -> bytes:
        """Encodes a NewOrderRequest to binary.

        Args:
            request: The NewOrderRequest object.

        Returns:
            bytes: The SBE encoded bytes.
        """
        raise NotImplementedError

    def encode_cancel_order_request(self, request: Any) -> bytes:
        """Encodes a CancelOrderRequest to binary.

        Args:
            request: The CancelOrderRequest object.

        Returns:
            bytes: The SBE encoded bytes.
        """
        raise NotImplementedError

    def encode_replace_order_request(self, request: Any) -> bytes:
        """Encodes a ReplaceOrderRequest to binary.

        Args:
            request: The ReplaceOrderRequest object.

        Returns:
            bytes: The SBE encoded bytes.
        """
        raise NotImplementedError

    def encode_session_transition(self, transition: Any) -> bytes:
        """Encodes a SessionTransition to binary.

        Args:
            transition: The SessionTransition object.

        Returns:
            bytes: The SBE encoded bytes.
        """
        raise NotImplementedError


class SbeDecoder:
    """Decodes SBE flat binary buffers into high-level domain objects."""

    def __init__(self) -> None:
        """Initializes the SbeDecoder."""
        raise NotImplementedError

    def decode_journal_record(self, data: bytes) -> Any:
        """Decodes binary data into a JournalRecord object.

        Args:
            data: SBE encoded bytes.

        Returns:
            Any: The decoded JournalRecord.
        """
        raise NotImplementedError

    def decode_execution_report(self, data: bytes) -> Any:
        """Decodes binary data into an ExecutionReport object.

        Args:
            data: SBE encoded bytes.

        Returns:
            Any: The decoded ExecutionReport.
        """
        raise NotImplementedError

    def decode_new_order_request(self, data: bytes) -> Any:
        """Decodes binary data into a NewOrderRequest object.

        Args:
            data: SBE encoded bytes.

        Returns:
            Any: The decoded NewOrderRequest.
        """
        raise NotImplementedError

    def decode_cancel_order_request(self, data: bytes) -> Any:
        """Decodes binary data into a CancelOrderRequest object.

        Args:
            data: SBE encoded bytes.

        Returns:
            Any: The decoded CancelOrderRequest.
        """
        raise NotImplementedError

    def decode_replace_order_request(self, data: bytes) -> Any:
        """Decodes binary data into a ReplaceOrderRequest object.

        Args:
            data: SBE encoded bytes.

        Returns:
            Any: The decoded ReplaceOrderRequest.
        """
        raise NotImplementedError

    def decode_session_transition(self, data: bytes) -> Any:
        """Decodes binary data into a SessionTransition object.

        Args:
            data: SBE encoded bytes.

        Returns:
            Any: The decoded SessionTransition.
        """
        raise NotImplementedError
