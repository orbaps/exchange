import subprocess
import time
from typing import Tuple, Optional

class SandboxProcess:
    """Wraps subprocess execution for the sandbox worker."""
    
    def __init__(self, cmd: list, preexec_fn=None, capture_stdout: bool = True, capture_stderr: bool = True):
        self.cmd = cmd
        self.preexec_fn = preexec_fn
        self.capture_stdout = capture_stdout
        self.capture_stderr = capture_stderr
        self.process: Optional[subprocess.Popen] = None
        self.start_time: float = 0.0

    def start(self) -> None:
        stdout_dest = subprocess.PIPE if self.capture_stdout else None
        stderr_dest = subprocess.PIPE if self.capture_stderr else None
        
        self.start_time = time.perf_counter()
        self.process = subprocess.Popen(
            self.cmd,
            stdout=stdout_dest,
            stderr=stderr_dest,
            preexec_fn=self.preexec_fn,
            text=True
        )

    def wait(self, timeout: float) -> Tuple[Optional[int], str, str, bool]:
        """Waits for the process to finish. Returns (exit_code, stdout, stderr, timed_out)."""
        if not self.process:
            raise RuntimeError("Process not started")
            
        stdout, stderr = "", ""
        timed_out = False
        try:
            out, err = self.process.communicate(timeout=timeout)
            stdout = out or ""
            stderr = err or ""
        except subprocess.TimeoutExpired:
            self.kill()
            out, err = self.process.communicate()
            stdout = out or ""
            stderr = err or ""
            timed_out = True
            
        return self.process.returncode, stdout, stderr, timed_out

    def terminate(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()

    def kill(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.kill()
