import sys
import logging

logger = logging.getLogger(__name__)

class ResourceLimiter:
    """Applies memory and CPU time limits to the current process."""
    
    @staticmethod
    def apply(memory_limit_mb: int, cpu_time_limit_seconds: int) -> None:
        if sys.platform != "linux" and sys.platform != "darwin":
            logger.debug(f"Resource limits (memory={memory_limit_mb}MB, cpu={cpu_time_limit_seconds}s) skipped on platform {sys.platform}.")
            return
            
        try:
            import resource
            
            # CPU Time Limit
            if cpu_time_limit_seconds > 0:
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit_seconds, cpu_time_limit_seconds))
                
            # Memory Limit
            if memory_limit_mb > 0:
                mem_bytes = memory_limit_mb * 1024 * 1024
                # RLIMIT_AS controls the maximum area (in bytes) of address space which may be taken by the process
                resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                
        except Exception as e:
            logger.warning(f"Failed to apply resource limits: {e}")

    @staticmethod
    def get_preexec_fn(memory_limit_mb: int, cpu_time_limit_seconds: int):
        """Returns a callable to be passed to subprocess.Popen(preexec_fn=...)."""
        if sys.platform == "win32":
            return None
            
        def preexec():
            ResourceLimiter.apply(memory_limit_mb, cpu_time_limit_seconds)
            
        return preexec
