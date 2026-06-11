import pytest
from federation.clock import DeterministicClock
from governance.models import CapacityForecast, FailureForecast, RiskSeverity, PartitionForecast
from governance.risk import RiskEngine

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def engine(clock):
    return RiskEngine(clock)

@pytest.mark.parametrize("i", range(30))
def test_assess_capacity_risk_critical(engine, i):
    forecast = CapacityForecast("n1", "cpu", 95.0 + (i*0.01), 100.0, 300, 1000)
    risk = engine.assess_capacity_risk(forecast)
    assert risk.severity == RiskSeverity.CRITICAL

@pytest.mark.parametrize("i", range(20))
def test_assess_failure_risk(engine, i):
    forecast = FailureForecast("n1", 0.9 + (i*0.001), 3600, 1000)
    risk = engine.assess_failure_risk(forecast)
    assert risk.severity == RiskSeverity.CRITICAL

@pytest.mark.parametrize("i", range(20))
def test_assess_partition_risk(engine, i):
    forecast = PartitionForecast(["n1"], 0.8 + (i*0.001), 1000)
    risk = engine.assess_partition_risk(forecast)
    assert risk.severity == RiskSeverity.CRITICAL
