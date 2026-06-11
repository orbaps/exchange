from benchmarking.models import BenchmarkProfile

def get_standard_profile() -> BenchmarkProfile:
    return BenchmarkProfile("STANDARD_PROFILE", target_qps=10000, duration_s=300, expected_latency_p99=0.5)

def get_stress_profile() -> BenchmarkProfile:
    return BenchmarkProfile("STRESS_PROFILE", target_qps=50000, duration_s=600, expected_latency_p99=1.5)
