from typing_extensions import Any


def to_plain(value) -> Any:
    """
    Recursively converts any value (including nested Gemini-specific
    types like MapComposite/RepeatedComposite) into "pure" Python
    types (dict, list, str, int, float, bool, None) that can be safely
    serialized to JSON for storage in a database.
    """
    if isinstance(value, dict) or hasattr(value, "items"):
        return {k: to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)) or hasattr(value, "__iter__") and not isinstance(value, (str, bytes)):
        try:
            return [to_plain(v) for v in value]
        except TypeError:
            return value
    return value
