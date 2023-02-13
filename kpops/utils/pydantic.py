# TODO: rename
import humps
from apischema import deserialize
from pydantic import BaseConfig
from typing_extensions import Self


def to_camel(field: str) -> str:
    if field == "schema_type":
        return field
    return humps.camelize(field)  # type: ignore


class CamelCaseConfig(BaseConfig):
    alias_generator = to_camel
    allow_population_by_field_name = True


# TODO: remove
class AllowExtraMixin:
    def __init__(self, **kwargs) -> None:  # allow extra fields passed as kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


# TODO: remove
# class FromDictMixin:
#     @classmethod
#     def from_dict(cls, d: dict) -> Self:
#         return cls(
#             **{k: v for k, v in d.items() if k in inspect.signature(cls).parameters}
#         )


class FromDictMixin:
    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return deserialize(cls, data, additional_properties=True)
