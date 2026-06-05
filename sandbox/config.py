from dataclasses import dataclass

@dataclass
class SandboxConfig:
    timeout_seconds: int = 10
    memory_limit_mb: int = 512
    cpu_time_limit_seconds: int = 10
    capture_stdout: bool = True
    capture_stderr: bool = True
