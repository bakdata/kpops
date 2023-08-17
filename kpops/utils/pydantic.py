from typing import Any

import humps
from pydantic import BaseConfig, BaseModel

from kpops.utils.docstring import describe_object


def to_camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    return humps.camelize(s)


def to_dash(s: str) -> str:
    """Convert PascalCase to dash-case."""
    return humps.depascalize(s).lower().replace("_", "-")


def to_dot(s: str) -> str:
    """Convert snake_case to dot.notation."""
    return s.replace("_", ".")


class CamelCaseConfig(BaseConfig):
    alias_generator = to_camel
    allow_population_by_field_name = True


class DescConfig(BaseConfig):
    @classmethod
    def schema_extra(cls, schema: dict[str, Any], model: type[BaseModel]) -> None:
        schema["description"] = describe_object(model.__doc__)
