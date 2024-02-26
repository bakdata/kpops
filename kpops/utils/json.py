import json


def is_jsonable(x):
    """Check whether a value is json-serializable."""
    try:
        json.dumps(x)
    except (TypeError, OverflowError):
        return False
    else:
        return True
