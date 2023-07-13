from typing import Any

import humps
from pydantic import BaseConfig, BaseModel, Extra, root_validator

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


class ExtraCamelCaseModel(BaseModel):
    @root_validator(pre=True)
    def extra_fields_to_camel(cls, values: dict[str, Any]) -> dict[str, Any]:
        camel_case_values = {}
        for key, value in values.items():
            camel_case_values[to_camel(key)] = value
        return camel_case_values

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.allow
