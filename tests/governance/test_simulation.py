import pytest
from federation.clock import DeterministicClock
from governance.simulation import SimulationEngine
from governance.models import SimulationConfig, SimulationType

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def engine(clock):
    return SimulationEngine(clock)

@pytest.mark.parametrize("i", range(1000))
def test_simulation_determinism_1000x(engine, i):
    config = SimulationConfig(SimulationType.PARTITION, ["node_1", "node_2", "node_3"], {})
    state = {"active_nodes": 5}
    
    result = engine.run_simulation(config, state)
    assert result.quorum_maintained is False
    assert result.success is True
    assert result.state_fingerprint == "cae77db0aa326696b8fb514300c296a05628284f19b1cd0e1d823e6ee037fcb6"
