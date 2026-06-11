"""Deployment guide generator with SHA-256 fingerprinting."""

from federation.clock import DeterministicClock
from typing import Dict, Any
import hashlib, json

class DeploymentGenerator:
    """Generates deterministic deployment guide documents."""
    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate(self) -> Dict[str, Any]:
        """Generate deployment_guide with SHA-256 fingerprint."""
        now = self.clock.now()
        doc = {"title": "deployment_guide", "providers": ["AWS", "Azure", "GCP"], "timestamp": now}
        doc["fingerprint"] = hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()
        return doc
