import humps
from pydantic import BaseConfig


def to_camel(field: str) -> str:
    return humps.camelize(field)  # type: ignore


class CamelCaseConfig(BaseConfig):
    alias_generator = to_camel
    allow_population_by_field_name = True
