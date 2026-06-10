from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional

class EvaluationDomain(Enum):
    CODING = "CODING"
    REASONING = "REASONING"
    MATHEMATICS = "MATHEMATICS"
    CYBERSECURITY = "CYBERSECURITY"
    QUANTUM = "QUANTUM"
    SYSTEMS = "SYSTEMS"

@dataclass
class Benchmark:
    """Ground truth model representing an evaluation task with domain requirements."""
    benchmark_id: str
    category: EvaluationDomain
    title: str
    description: str
    seed: int
    max_score: float
    expected_output: str
    evaluation_rules: List[str] = field(default_factory=list)
    timeout_ms: int = 5000
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1  # version tracking to prevent invalidation

@dataclass
class BenchmarkSuite:
    """Collection of related benchmark cases to evaluate specific capability dimensions."""
    suite_id: str
    name: str
    benchmarks: List[Benchmark] = field(default_factory=list)


class BenchmarkRegistry:
    """Central registry for discovering, managing, and looking up benchmarks."""
    
    def __init__(self):
        self._benchmarks: Dict[str, Benchmark] = {}

    def register(self, benchmark: Benchmark):
        self._benchmarks[benchmark.benchmark_id] = benchmark

    def unregister(self, benchmark_id: str):
        if benchmark_id in self._benchmarks:
            del self._benchmarks[benchmark_id]

    def get_benchmark(self, benchmark_id: str) -> Optional[Benchmark]:
        return self._benchmarks.get(benchmark_id)

    def list_benchmarks(self) -> List[Benchmark]:
        return list(self._benchmarks.values())

    def version(self, benchmark_id: str) -> Optional[int]:
        b = self.get_benchmark(benchmark_id)
        return b.version if b else None

    def search(self, query: str) -> List[Benchmark]:
        q = query.lower()
        return [
            b for b in self._benchmarks.values()
            if q in b.title.lower() or q in b.description.lower() or q in b.benchmark_id.lower()
        ]

    def tags(self, tag: str) -> List[Benchmark]:
        return [
            b for b in self._benchmarks.values()
            if tag in b.metadata.get("tags", [])
        ]

