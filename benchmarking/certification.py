"""Certification module for deterministic platform certification.

Certification Fingerprint Formula:
    hash_fingerprint = SHA256(json.dumps({
        "passed": bool,
        "benchmark_fingerprint": str,
        "timestamp": float
    }, sort_keys=True))

The sort_keys=True parameter eliminates Python dictionary memory-order variance.
The cert_id is derived as: f"cert_{timestamp}_{hash_fingerprint[:8]}"
"""

from federation.clock import DeterministicClock
from benchmarking.models import CertificationResult
from typing import Dict, Any
import hashlib
import json


class CertificationManager:
    """Evaluates benchmark results and issues deterministic platform certificates.

    The certification hash is computed as:
        SHA256(json.dumps({"passed": bool, "benchmark_fingerprint": str, "timestamp": float}, sort_keys=True))

    This guarantees that identical benchmark inputs always produce identical
    certification fingerprints regardless of execution environment.
    """

    def __init__(self, clock: DeterministicClock):
        self.clock = clock

    def evaluate_benchmark(self, benchmark_result: Dict[str, Any]) -> CertificationResult:
        """Evaluate a benchmark result and produce a CertificationResult.

        Args:
            benchmark_result: Dict containing at minimum 'qps_achieved',
                'latency_p99', and 'fingerprint' keys.

        Returns:
            CertificationResult with deterministic hash_fingerprint computed as:
                SHA256(json.dumps({
                    "passed": qps_achieved >= 1000 and latency_p99 <= 1.0,
                    "benchmark_fingerprint": benchmark_result["fingerprint"],
                    "timestamp": clock.now()
                }, sort_keys=True))
        """
        now = self.clock.now()
        passed = benchmark_result["qps_achieved"] >= 1000 and benchmark_result["latency_p99"] <= 1.0

        cert_data = {
            "passed": passed,
            "benchmark_fingerprint": benchmark_result["fingerprint"],
            "timestamp": now
        }
        cert_str = json.dumps(cert_data, sort_keys=True)
        cert_hash = hashlib.sha256(cert_str.encode("utf-8")).hexdigest()

        return CertificationResult(
            cert_id=f"cert_{now}_{cert_hash[:8]}",
            passed=passed,
            score=benchmark_result["qps_achieved"] / benchmark_result["latency_p99"],
            hash_fingerprint=cert_hash,
            timestamp=now
        )
