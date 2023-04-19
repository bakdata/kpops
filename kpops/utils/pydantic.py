from typing import Any

import humps
from pydantic import BaseConfig, BaseModel

from kpops.utils.docstring import describe_class


def to_camel(field: str) -> str:
    if field == "schema_type":
        return field
    return humps.camelize(field)  # type: ignore


class CamelCaseConfig(BaseConfig):
    alias_generator = to_camel
    allow_population_by_field_name = True


class DescConfig(BaseConfig):
    @staticmethod
    def schema_extra(schema: dict[str, Any], model: type[BaseModel]) -> None:  # type: ignore[override]
        schema["description"] = describe_class(model.__doc__)
