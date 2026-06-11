import pytest
from federation.clock import DeterministicClock
from governance.prediction import PredictionEngine
from governance.models import CapacityForecast, FailureForecast

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

@pytest.fixture
def engine(clock):
    return PredictionEngine(clock)

@pytest.mark.parametrize("i", range(30))
def test_forecast_capacity_linear(engine, i):
    history = [10.0 + (i * 0.1), 20.0 + (i * 0.1), 30.0 + (i * 0.1), 40.0 + (i * 0.1)]
    forecast = engine.forecast_capacity("node_1", "cpu", history)
    assert forecast.node_id == "node_1"
    assert forecast.metric == "cpu"
    assert forecast.projected_value_1h > 100.0
    assert forecast.time_to_bottleneck_s is not None

@pytest.mark.parametrize("i", range(20))
def test_forecast_failure_healthy(engine, i):
    history = [{"status": "HEALTHY"} for _ in range(10)]
    forecast = engine.forecast_failure("node_1", history)
    assert forecast.failure_probability == 0.0

@pytest.mark.parametrize("i", range(20))
def test_forecast_failure_degraded(engine, i):
    history = [{"status": "DEGRADED"} for _ in range(10)]
    forecast = engine.forecast_failure("node_1", history)
    assert forecast.failure_probability > 0.8
    assert forecast.time_to_failure_s == 3600.0

@pytest.mark.parametrize("i", range(20))
def test_forecast_partition(engine, i):
    history = [{"node_id": "n1", "missed_heartbeats": 5}] * 10
    forecast = engine.forecast_partition(history)
    assert forecast.probability == 0.75
    assert len(forecast.affected_nodes) == 10
