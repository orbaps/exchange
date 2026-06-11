"""Competition demo report generator with SHA-256 fingerprinting."""

from federation.clock import DeterministicClock
from typing import Dict, Any
import hashlib, json

class CompetitionGenerator:
    """Generates deterministic competition submission documents."""
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate(self) -> Dict[str, Any]:
        """Generate competition_demo with SHA-256 fingerprint."""
        now = self.clock.now()
        doc = {"title": "competition_demo", "showcases": 3, "timestamp": now}
        doc["fingerprint"] = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
        return doc
