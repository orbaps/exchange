import os
import json
import ast
from typing import Optional

from submission.metadata import SubmissionMetadata
from submission.result import SubmissionLoadResult

class SubmissionValidator:
    """Validates contestant submission structure without executing untrusted code."""

    @staticmethod
    def validate(submission_dir: str) -> SubmissionLoadResult:
        errors = []
        metadata = None

        metadata_path = os.path.join(submission_dir, "metadata.json")
        engine_path = os.path.join(submission_dir, "engine.py")

        # 1. Validate structure
        if not os.path.isdir(submission_dir):
            return SubmissionLoadResult(False, errors=[f"Directory {submission_dir} does not exist."])
            
        if not os.path.isfile(metadata_path):
            errors.append("Missing metadata.json")
            
        if not os.path.isfile(engine_path):
            errors.append("Missing engine.py")

        if errors:
            return SubmissionLoadResult(False, errors=errors)

        # 2. Validate metadata.json
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            required_keys = ["team_name", "engine_class", "version"]
            for key in required_keys:
                if key not in data or not isinstance(data[key], str) or not data[key].strip():
                    errors.append(f"Invalid or missing '{key}' in metadata.json")
                    
            if errors:
                return SubmissionLoadResult(False, errors=errors)

            metadata = SubmissionMetadata(
                team_name=data["team_name"].strip(),
                engine_class=data["engine_class"].strip(),
                version=data["version"].strip()
            )
        except json.JSONDecodeError:
            return SubmissionLoadResult(False, errors=["metadata.json is not valid JSON."])
        except Exception as e:
            return SubmissionLoadResult(False, errors=[f"Failed to read metadata.json: {e}"])

        # 3. Validate engine.py contains the target class via AST (no execution)
        try:
            with open(engine_path, 'r', encoding='utf-8') as f:
                engine_code = f.read()
                
            tree = ast.parse(engine_code)
            class_found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == metadata.engine_class:
                    class_found = True
                    break
                    
            if not class_found:
                errors.append(f"Class '{metadata.engine_class}' not found in engine.py")
        except SyntaxError as e:
            errors.append(f"Syntax error in engine.py: {e}")
        except Exception as e:
            errors.append(f"Failed to parse engine.py: {e}")

        if errors:
            return SubmissionLoadResult(False, metadata=metadata, errors=errors)

        return SubmissionLoadResult(True, metadata=metadata)
