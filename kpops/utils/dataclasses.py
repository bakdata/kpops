from dataclasses import is_dataclass


def is_dataclass_instance(obj: object) -> bool:
    return is_dataclass(obj) and not isinstance(obj, type)
