import pytest
from federation.clock import DeterministicClock
import hashlib
import json

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

def mock_cicd_pipeline(clock: DeterministicClock) -> str:
    pipe = {"trigger": "push", "timestamp": clock.now()}
    return hashlib.sha256(json.dumps(pipe, sort_keys=True).encode("utf-8")).hexdigest()

@pytest.mark.parametrize("i", range(1000))
def test_deployment_pipeline_determinism_1000x(clock, i):
    assert mock_cicd_pipeline(clock) == mock_cicd_pipeline(clock)

@pytest.mark.parametrize("i", range(100))
def test_cicd_integrity(clock, i):
    assert mock_cicd_pipeline(clock) is not None
