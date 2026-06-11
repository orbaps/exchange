import pytest
from federation.clock import DeterministicClock
from governance.governance import GovernanceEngine

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def engine(clock):
    return GovernanceEngine(clock)

@pytest.mark.parametrize("i", range(10000))
def test_governance_determinism_10000x(engine, i):
    state = {"active_nodes": 5, "current_metrics": {"cpu": 85.0}}
    hist_metrics = {"cpu_history": {"node_1": [70.0, 75.0, 80.0, 85.0]}}
    
    engine.process_system_state(state, hist_metrics)
    
    records = engine.journal.get_all()
    assert len(records) > 0
    assert records[-1].decision.action_type == "THROTTLE_WORKLOAD"
