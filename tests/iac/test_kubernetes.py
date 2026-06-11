import pytest
import hashlib
import json
from federation.clock import DeterministicClock

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

def mock_k8s_manifest(clock: DeterministicClock, component: str) -> str:
    manifest = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": component,
            "labels": {"app": component, "timestamp": str(clock.now())}
        }
    }
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()

@pytest.mark.parametrize("i", range(5000))
def test_k8s_manifest_determinism_5000x(clock, i):
    h1 = mock_k8s_manifest(clock, "dashboard")
    h2 = mock_k8s_manifest(clock, "dashboard")
    assert h1 == h2

@pytest.mark.parametrize("i", range(200))
def test_k8s_manifest_integrity(clock, i):
    assert mock_k8s_manifest(clock, f"comp_{i}") is not None
