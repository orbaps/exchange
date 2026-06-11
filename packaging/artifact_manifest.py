"""Artifact manifest generator for competition submission tracking.

Produces a deterministic manifest.json with SHA-256 fingerprinting.
"""

from federation.clock import DeterministicClock
from typing import Dict, Any, List
import hashlib
import json


class ArtifactManifest:
    """Generates a deterministic artifact manifest for the submission.

    Args:
        clock: DeterministicClock instance for timestamping the manifest.
    """

    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def generate(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate the artifact manifest.

        Args:
            documents: List of document dicts, each with a 'title' and 'fingerprint'.

        Returns:
            Dict with entries (sorted by title), count, timestamp,
            and a SHA-256 fingerprint of the manifest.
        """
        now = self.clock.now()
        entries = sorted(
            [{"title": d["title"], "fingerprint": d["fingerprint"]} for d in documents],
            key=lambda x: x["title"]
        )
        result = {
            "entries": entries,
            "count": len(entries),
            "timestamp": now
        }
        result_str = json.dumps(result, sort_keys=True)
        result["fingerprint"] = hashlib.sha256(result_str.encode("utf-8")).hexdigest()
        return result
