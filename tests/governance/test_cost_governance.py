import pytest
from federation.clock import DeterministicClock
from governance.cloud_cost import CloudCostGovernance
from strategic.cost_optimizer import CostOptimizer, ResourceCostProfile

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def cost_gov(clock):
    return CloudCostGovernance(clock)

@pytest.fixture
def cost_opt(clock):
    return CostOptimizer(clock)

@pytest.mark.parametrize("i", range(100))
def test_cloud_cost_forecast_determinism(cost_gov, i):
    forecast = cost_gov.generate_forecast({"active_nodes": 10, "tournaments_run": 5})
    assert forecast.projected_monthly_cost == 10 * 50.0 * 1.05
    assert forecast.cost_per_tournament == forecast.projected_monthly_cost / 5

@pytest.mark.parametrize("i", range(200))
def test_cost_optimizer_determinism(cost_opt, i):
    profiles = [
        ResourceCostProfile("c1", 1000.0, 50.0),
        ResourceCostProfile("c2", 2000.0, 150.0),
        ResourceCostProfile("c3", 1500.0, 200.0)
    ]
    plan = cost_opt.optimize_cluster_costs(profiles)
    assert plan.target_savings == 350.0
    assert len(plan.actions) == 2
    assert plan.actions[0]["cluster"] == "c3"  # sorted by potential
    assert plan.actions[1]["cluster"] == "c2"
