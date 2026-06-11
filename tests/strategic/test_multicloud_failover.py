import pytest
from federation.clock import DeterministicClock
from strategic.multicloud import MultiCloudFailoverManager

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def failover(clock):
    return MultiCloudFailoverManager(clock)

@pytest.mark.parametrize("i", range(500))
def test_multicloud_evacuation_determinism(failover, i):
    plan = failover.simulate_evacuation("AWS", ["AWS", "Azure", "GCP"])
    assert plan.source_provider == "AWS"
    # azure should be chosen as it's sorted after removing AWS
    assert plan.target_provider == "Azure"
    assert len(plan.actions) == 3
    assert plan.actions[0]["action"] == "PROVISION_CLUSTER"
