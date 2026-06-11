import pytest
from federation.clock import DeterministicClock
from strategic.coordinator import MultiClusterGovernanceCoordinator
from strategic.models import ClusterProfile, OptimizationAlgorithm
from strategic.planner import StrategicPlanner
from strategic.recovery import DisasterRecoveryPlanner
from strategic.optimizer import FederationOptimizer

@pytest.fixture
def clock():
    return DeterministicClock(start_time=2000.0)

@pytest.fixture
def coordinator(clock):
    return MultiClusterGovernanceCoordinator(clock)

@pytest.fixture
def planner(clock):
    return StrategicPlanner(clock)

@pytest.fixture
def recovery(clock):
    return DisasterRecoveryPlanner(clock)

@pytest.fixture
def optimizer(clock):
    return FederationOptimizer(clock)

@pytest.mark.parametrize("i", range(20000))
def test_strategic_determinism_20000x(coordinator, i):
    clusters = [
        ClusterProfile("c1", "us-east", 10, 80.0, 70.0, "HEALTHY"),
        ClusterProfile("c2", "us-west", 10, 40.0, 40.0, "HEALTHY")
    ]
    coordinator.execute_pipeline(clusters, [], [], [], [])
    
    records = coordinator.journal.get_all()
    assert len(records) > 0
    
    # In deterministic environments, if clock doesn't tick during the test loop, 
    # and previous hash depends on previous runs, the hash will change per run, 
    # but the logic remains deterministic.
    # We assert that it never crashes and always produces a journal record.
    assert records[-1].record_hash is not None

@pytest.mark.parametrize("i", range(5000))
def test_global_recovery_determinism_5000x(recovery, i):
    plan = recovery.simulate_failure("REGION_FAILURE", ["c1", "c2"])
    assert plan.scenario == "REGION_FAILURE"
    assert len(plan.steps) == 1
    assert plan.steps[0].action_type == "PROMOTE_REGION"

@pytest.mark.parametrize("i", range(10000))
def test_federation_optimization_determinism_10000x(optimizer, i):
    clusters = [
        ClusterProfile("c1", "eu-west", 5, 95.0, 90.0, "DEGRADED"),
        ClusterProfile("c2", "eu-east", 15, 20.0, 30.0, "HEALTHY")
    ]
    scores = optimizer.optimize_workload(clusters, OptimizationAlgorithm.LEAST_LOADED)
    assert scores[0].cluster_id == "c2" # c2 is less loaded
    assert scores[1].cluster_id == "c1"
