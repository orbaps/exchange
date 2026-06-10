import sys
import os
import json
import tempfile
import logging
import time
from typing import Optional

from benchmarking.scenario import BenchmarkScenario
from submission.metadata import SubmissionManifest

from sandbox.config import SandboxConfig
from sandbox.result import SandboxResult
from sandbox.limits import ResourceLimiter
from sandbox.process import SandboxProcess
from sandbox.protocol import WorkerRequest, WorkerResponse
from sandbox.logging import SandboxEvent, SandboxEventType

logger = logging.getLogger(__name__)

class SandboxRunner:
    """Executes a contestant in an isolated subprocess sandbox."""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()

    def run_submission(self, manifest: SubmissionManifest, scenario: BenchmarkScenario) -> SandboxResult:
        """Helper to run a full scenario against a submission, writing temp files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            events_path = os.path.join(temp_dir, "events.json")
            
            # Serialize events
            events_list = [
                {
                    "event_type": event.event_type,
                    "payload": event.payload
                }
                for event in scenario.events
            ]
            
            with open(events_path, "w") as f:
                json.dump(events_list, f)
                
            request = WorkerRequest(
                submission_path=manifest.submission_path,
                events_path=events_path,
                output_path=temp_dir
            )
            
            return self.run_worker(request)

    def run_worker(self, request: WorkerRequest) -> SandboxResult:
        """Runs the worker subprocess using the provided request."""
        worker_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker.py")
        
        cmd = [
            sys.executable, worker_script,
            "--submission-path", request.submission_path,
            "--events-path", request.events_path,
            "--output-path", request.output_path
        ]
        
        preexec_fn = ResourceLimiter.get_preexec_fn(
            self.config.memory_limit_mb,
            self.config.cpu_time_limit_seconds
        )
        
        process = SandboxProcess(
            cmd=cmd,
            preexec_fn=preexec_fn,
            capture_stdout=self.config.capture_stdout,
            capture_stderr=self.config.capture_stderr
        )
        
        # Log START
        logger.info(f"Sandbox STARTED for {request.submission_path}")
        
        process.start()
        exit_code, stdout, stderr, timed_out = process.wait(self.config.timeout_seconds)
        
        # Determine status
        crashed = False
        success = False
        exception_type = None
        exception_message = None
        
        if timed_out:
            logger.warning(f"Sandbox TIMED_OUT for {request.submission_path}")
        else:
            if exit_code != 0:
                crashed = True
                logger.error(f"Sandbox CRASHED for {request.submission_path} with exit_code={exit_code}")
            else:
                success = True
                logger.info(f"Sandbox FINISHED for {request.submission_path}")

        # Try to read execution.json to get more structured errors if worker generated it
        execution_file = os.path.join(request.output_path, "execution.json")
        execution_stats = None
        
        if os.path.exists(execution_file):
            try:
                with open(execution_file, "r") as f:
                    exec_data = json.load(f)
                    
                if not exec_data.get("success", False):
                    success = False
                    if exec_data.get("error"):
                        crashed = True
                        err_parts = exec_data["error"].split(":", 1)
                        if len(err_parts) > 1:
                            exception_type = err_parts[0].strip()
                            exception_message = err_parts[1].strip()
                        else:
                            exception_message = exec_data["error"]
                            
                worker_runtime_ms = exec_data.get("runtime_ms", 0.0)
                event_count = exec_data.get("event_count", 0)
                if worker_runtime_ms > 0:
                    from telemetry.execution import ExecutionStatistics
                    eps = event_count / (worker_runtime_ms / 1000.0)
                    execution_stats = ExecutionStatistics(
                        runtime_ms=worker_runtime_ms,
                        event_count=event_count,
                        eps=eps
                    )
            except Exception as e:
                logger.error(f"Failed to parse execution.json: {e}")
                
        runtime_ms = (time.perf_counter() - process.start_time) * 1000 if process.start_time else 0.0
        # NOTE: wait(), start_time are used but process.start_time is float from time.perf_counter, let's fix import time in this file!
        
        if execution_stats:
            execution_stats.sandbox_overhead_ms = max(0.0, runtime_ms - execution_stats.runtime_ms)
            
        return SandboxResult(
            success=success and not timed_out,
            exit_code=exit_code,
            runtime_ms=runtime_ms,
            timed_out=timed_out,
            crashed=crashed,
            stdout=stdout,
            stderr=stderr,
            exception_type=exception_type,
            exception_message=exception_message,
            execution_stats=execution_stats
        )
