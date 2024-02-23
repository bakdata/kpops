import json


def is_jsonable(x):
    try:
        json.dumps(x)
    except (TypeError, OverflowError):
        return False
    else:
        return True
