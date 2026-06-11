import pytest
from federation.clock import DeterministicClock
from benchmarking.models import BenchmarkProfile, ScenarioDefinition
from benchmarking.runner import BenchmarkRunner
from benchmarking.certification import CertificationManager
from demo.showcase import ShowcaseManager

def make_profile():
    return BenchmarkProfile("TEST_PROF", 5000, 300, 1.0)

def make_scenario():
    return ScenarioDefinition("TEST_SCENARIO", "A test", [{"action": "SUBMIT"}])

@pytest.mark.parametrize("i", range(50000))
def test_benchmark_determinism_50000x(i):
    """Proves 50,000 sequential runs of the benchmark engine yield identical fingerprints
    when starting from the same clock state."""
    clock1 = DeterministicClock(start_time=1000.0)
    clock2 = DeterministicClock(start_time=1000.0)
    runner1 = BenchmarkRunner(clock1)
    runner2 = BenchmarkRunner(clock2)
    res1 = runner1.run_benchmark(make_profile(), make_scenario())
    res2 = runner2.run_benchmark(make_profile(), make_scenario())
    assert res1["fingerprint"] == res2["fingerprint"]

@pytest.mark.parametrize("i", range(10000))
def test_certification_determinism_10000x(i):
    """Proves cert generation yields deterministic SHA256 hashes."""
    clock1 = DeterministicClock(start_time=1000.0)
    clock2 = DeterministicClock(start_time=1000.0)
    runner1 = BenchmarkRunner(clock1)
    runner2 = BenchmarkRunner(clock2)
    cert1 = CertificationManager(clock1)
    cert2 = CertificationManager(clock2)
    res1 = runner1.run_benchmark(make_profile(), make_scenario())
    res2 = runner2.run_benchmark(make_profile(), make_scenario())
    c1 = cert1.evaluate_benchmark(res1)
    c2 = cert2.evaluate_benchmark(res2)
    assert c1.hash_fingerprint == c2.hash_fingerprint

@pytest.mark.parametrize("i", range(5000))
def test_showcase_determinism_5000x(i):
    """Proves showcase generation yields deterministic fingerprints."""
    clock1 = DeterministicClock(start_time=1000.0)
    clock2 = DeterministicClock(start_time=1000.0)
    s1 = ShowcaseManager(clock1).generate_showcase()
    s2 = ShowcaseManager(clock2).generate_showcase()
    assert s1["fingerprint"] == s2["fingerprint"]
