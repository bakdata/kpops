import json
from typing import Any


def is_jsonable(input: Any) -> bool:
    """Check whether a value is json-serializable.

    :param input: Value to be checked.
    """
    try:
        json.dumps(input)
    except (TypeError, OverflowError):
        return False
    else:
        return True
