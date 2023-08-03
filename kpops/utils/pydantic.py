from typing import Any

import humps
from pydantic import BaseConfig, BaseModel

from kpops.utils.docstring import describe_object


def to_camel(s: str) -> str:
    return humps.camelize(s)


def to_dash(s: str) -> str:
    if s.upper() == s:
        return s.lower()
    return humps.depascalize(s).replace("_", "-")


class CamelCaseConfig(BaseConfig):
    alias_generator = to_camel
    allow_population_by_field_name = True


class DescConfig(BaseConfig):
    @staticmethod
    def schema_extra(schema: dict[str, Any], model: type[BaseModel]) -> None:
        schema["description"] = describe_object(model.__doc__)
