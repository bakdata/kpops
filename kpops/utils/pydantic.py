from typing import Any

import humps
from pydantic import BaseConfig, BaseModel

from kpops.utils.docstring import describe_object


def to_camel(field: str) -> str:
    if field == "schema_type":
        return field
    return humps.camelize(field)


class CamelCaseConfig(BaseConfig):
    alias_generator = to_camel
    allow_population_by_field_name = True


class DescConfig(BaseConfig):
    @staticmethod
    def schema_extra(schema: dict[str, Any], model: type[BaseModel]) -> None:
        schema["description"] = describe_object(model.__doc__)
