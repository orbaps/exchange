"""Certification report generator with SHA-256 fingerprinting."""

from federation.clock import DeterministicClock
from typing import Dict, Any
import hashlib, json

class CertificationGenerator:
    """Generates deterministic certification report documents."""
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate(self) -> Dict[str, Any]:
        """Generate certification_report with SHA-256 fingerprint."""
        now = self.clock.now()
        doc = {"title": "certification_report", "certified": True, "timestamp": now}
        doc["fingerprint"] = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
        return doc
