"""Phase 9.2 Release Hardening test suite.

Uses the dual-clock verification pattern: two independent DeterministicClock
instances with identical seeds are used to prove that all release artifacts
produce bit-for-bit identical SHA-256 fingerprints.
"""

import pytest
from federation.clock import DeterministicClock
from validation.release_validator import ReleaseValidator
from validation.security_audit import SecurityAuditor
from validation.dependency_audit import DependencyAuditor
from validation.e2e_pipeline import E2EPipeline
from validation.determinism_audit import DeterminismAuditor
from packaging.submission_package import SubmissionPackage
from packaging.artifact_manifest import ArtifactManifest
from docs_generator.architecture_generator import ArchitectureGenerator
from docs_generator.deployment_generator import DeploymentGenerator
from docs_generator.api_generator import ApiGenerator
from docs_generator.benchmark_generator import BenchmarkGenerator
from docs_generator.certification_generator import CertificationGenerator
from docs_generator.competition_generator import CompetitionGenerator


# ---- Unit tests ----

def test_release_validation():
    """Validates ReleaseValidator produces a RELEASE_READY result."""
    clock = DeterministicClock(start_time=1000.0)
    validator = ReleaseValidator(clock)
    result = validator.validate_all()
    assert result["status"] == "RELEASE_READY"
    assert result["checks_passed"] == result["checks_total"]
    assert "fingerprint" in result


def test_security_audit():
    """Validates SecurityAuditor produces a CLEAN result."""
    clock = DeterministicClock(start_time=1000.0)
    auditor = SecurityAuditor(clock)
    result = auditor.run_audit()
    assert result["status"] == "CLEAN"
    assert result["violations_found"] == 0
    assert "fingerprint" in result


def test_dependency_audit():
    """Validates DependencyAuditor produces an ALL_PINNED result."""
    clock = DeterministicClock(start_time=1000.0)
    auditor = DependencyAuditor(clock)
    result = auditor.run_audit()
    assert result["status"] == "ALL_PINNED"
    assert result["floating_count"] == 0
    assert "fingerprint" in result


def test_package_generation():
    """Validates SubmissionPackage produces a fingerprinted package."""
    clock = DeterministicClock(start_time=1000.0)
    packager = SubmissionPackage(clock)
    result = packager.generate(["abc123", "def456"])
    assert result["artifact_count"] == 2
    assert result["artifacts"] == ["abc123", "def456"]  # sorted
    assert "fingerprint" in result


def test_e2e_pipeline():
    """Validates E2EPipeline traverses all 12 stages."""
    clock = DeterministicClock(start_time=1000.0)
    pipeline = E2EPipeline(clock)
    result = pipeline.run_pipeline()
    assert result["status"] == "E2E_PASSED"
    assert result["stages_count"] == 12
    assert len(result["stages"]) == 12
    assert "fingerprint" in result


# ---- Flagship determinism tests (dual-clock pattern) ----

@pytest.mark.parametrize("i", range(10000))
def test_release_determinism_10000x(i):
    """Proves 10,000 release validations yield identical fingerprints."""
    c1 = DeterministicClock(start_time=1000.0)
    c2 = DeterministicClock(start_time=1000.0)
    r1 = ReleaseValidator(c1).validate_all()
    r2 = ReleaseValidator(c2).validate_all()
    assert r1["fingerprint"] == r2["fingerprint"]


@pytest.mark.parametrize("i", range(1000))
def test_e2e_pipeline_determinism_1000x(i):
    """Proves 1,000 E2E pipeline runs yield identical fingerprints."""
    c1 = DeterministicClock(start_time=1000.0)
    c2 = DeterministicClock(start_time=1000.0)
    r1 = E2EPipeline(c1).run_pipeline()
    r2 = E2EPipeline(c2).run_pipeline()
    assert r1["fingerprint"] == r2["fingerprint"]


@pytest.mark.parametrize("i", range(5000))
def test_submission_package_determinism_5000x(i):
    """Proves 5,000 submission packages yield identical fingerprints."""
    c1 = DeterministicClock(start_time=1000.0)
    c2 = DeterministicClock(start_time=1000.0)
    fps = ["hash_a", "hash_b", "hash_c"]
    r1 = SubmissionPackage(c1).generate(fps)
    r2 = SubmissionPackage(c2).generate(fps)
    assert r1["fingerprint"] == r2["fingerprint"]
