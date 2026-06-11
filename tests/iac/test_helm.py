import pytest
from federation.clock import DeterministicClock
import hashlib
import json

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

def mock_helm_chart(clock: DeterministicClock) -> str:
    chart = {"name": "iicpc-platform", "version": "1.0.0", "timestamp": clock.now()}
    return hashlib.sha256(json.dumps(chart, sort_keys=True).encode("utf-8")).hexdigest()

@pytest.mark.parametrize("i", range(100))
def test_helm_chart_determinism_100x(clock, i):
    assert mock_helm_chart(clock) == mock_helm_chart(clock)
