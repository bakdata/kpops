from typing import Any
import humps
from kpops.utils.docstring import describe_class
from pydantic import BaseConfig, BaseModel


def to_camel(field: str) -> str:
    if field == "schema_type":
        return field
    return humps.camelize(field)  # type: ignore


class CamelCaseConfig(BaseConfig):
    alias_generator = to_camel
    allow_population_by_field_name = True

class DescConfig(BaseConfig):
        @staticmethod
        def schema_extra(schema: dict[str, Any], model: type[BaseModel]):
            schema["description"] = describe_class(model)
