import os
import sys
import importlib.util
from typing import Any

from submission.metadata import SubmissionMetadata

class SubmissionLoader:
    """Dynamically loads and instantiates contestant engine code."""
    
    @staticmethod
    def load(submission_dir: str, metadata: SubmissionMetadata) -> Any:
        """Dynamically imports engine.py and returns an instance of the target class."""
        engine_path = os.path.join(submission_dir, "engine.py")
        
        # Ensure the directory is in sys.path temporarily so absolute imports within the contestant code might work
        if submission_dir not in sys.path:
            sys.path.insert(0, submission_dir)
            
        try:
            module_name = f"submission_{metadata.team_name.replace(' ', '_')}"
            spec = importlib.util.spec_from_file_location(module_name, engine_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load spec for {engine_path}")
                
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            engine_class = getattr(module, metadata.engine_class)
            return engine_class()
        finally:
            if submission_dir in sys.path:
                sys.path.remove(submission_dir)
