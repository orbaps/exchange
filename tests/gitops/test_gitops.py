import pytest
from federation.clock import DeterministicClock
from gitops.gitops import GitOpsEngine
from gitops.deployment_sync import DeploymentSync
from gitops.rollback_manager import RollbackManager

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def engine(clock):
    return GitOpsEngine(clock)

@pytest.fixture
def sync(clock):
    return DeploymentSync(clock)

@pytest.fixture
def rollback(clock):
    return RollbackManager(clock)

@pytest.mark.parametrize("i", range(100))
def test_drift_detection(engine, i):
    state_a = {"version": "v1"}
    state_b = {"version": "v2"}
    assert engine.check_drift(state_a, state_b) is True
    assert engine.check_drift(state_a, state_a) is False

@pytest.mark.parametrize("i", range(500))
def test_sync_determinism(sync, i):
    manifest = {"api": "apps/v1"}
    h1 = sync.sync("prod", manifest)
    h2 = sync.sync("prod", manifest)
    assert h1 == h2

def test_rollback(rollback):
    rollback.record_deployment("d1", {"v": 1})
    rollback.record_deployment("d2", {"v": 2})
    state = rollback.generate_rollback(1)
    assert state == {"v": 1}
