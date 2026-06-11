import pytest
from federation.clock import DeterministicClock
from governance.simulation import SimulationEngine
from governance.evolution import PolicyEvolutionEngine
from governance.models import VersionedPolicy, PolicyType

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def sim_engine(clock):
    return SimulationEngine(clock)

@pytest.fixture
def evo_engine(sim_engine):
    return PolicyEvolutionEngine(sim_engine)

@pytest.mark.parametrize("i", range(5000))
def test_policy_evolution_determinism_5000x(evo_engine, i):
    policy = VersionedPolicy("pol_1", 1, PolicyType.THRESHOLD, {"metric": "cpu", "value": 80.0, "operator": ">"}, True)
    state = {"active_nodes": 5}
    
    evolved = evo_engine.evolve_policy(policy, state)
    
    assert evolved is not None
    assert evolved.version == 2
    assert evolved.rules["value"] == 76.0
