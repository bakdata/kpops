from typing import Any

import humps
from pydantic import BaseModel, ConfigDict

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

def schema_extra(schema: dict[str, Any], model: type[BaseModel]) -> None:
    schema["description"] = describe_object(model.__doc__)

class CamelCaseConfigModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class DescConfigModel(BaseModel):
    model_config = ConfigDict(
        json_schema_extra=schema_extra
    )
