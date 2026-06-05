import dataclasses

def to_dict(obj):
    """
    Recursively converts a dataclass to a dictionary, including enums.
    """
    if dataclasses.is_dataclass(obj):
        return {k: to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_dict(v) for v in obj]
    elif hasattr(obj, "name"): # Enum
        return obj.name
    else:
        return obj
