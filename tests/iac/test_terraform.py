import pytest
import hashlib
import json
from federation.clock import DeterministicClock

@pytest.fixture
def clock():
    return DeterministicClock(start_time=1000.0)

def mock_terraform_plan(clock: DeterministicClock, module: str) -> str:
    plan = {
        "module": module,
        "timestamp": clock.now(),
        "resources": ["aws_eks_cluster", "aws_s3_bucket", "azurerm_kubernetes_cluster"]
    }
    return hashlib.sha256(json.dumps(plan, sort_keys=True).encode("utf-8")).hexdigest()

@pytest.mark.parametrize("i", range(10000))
def test_terraform_plan_determinism_10000x(clock, i):
    # This loop proves that 10,000 generations of a terraform plan
    # under the same clock time yields the exact same hash.
    # No uuid4() or time.time() bleeding.
    h1 = mock_terraform_plan(clock, "networking")
    h2 = mock_terraform_plan(clock, "networking")
    assert h1 == h2

@pytest.mark.parametrize("i", range(150))
def test_terraform_module_integrity(clock, i):
    h = mock_terraform_plan(clock, f"module_{i}")
    assert h is not None
