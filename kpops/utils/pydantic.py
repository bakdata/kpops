from typing import Any

import humps
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake

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


def by_alias(field_name: str, model: BaseModel) -> str:
    """Return field alias if exists else field name.

    :param field_name: Name of the field to get alias of
    :param model: Model that owns the field
    """
    return model.model_fields.get(field_name, Field()).alias or field_name


def exclude_by_value(
    dumped_model: dict[str, Any], *excluded_values: Any
) -> dict[str, Any]:
    """Strip all key-value pairs with certain values.

    :param dumped_model: Dumped model
    :param excluded_values: Excluded field values
    :return: Dumped model without excluded fields
    """
    return {
        field_name: field_value
        for field_name, field_value in dumped_model.items()
        if field_value not in excluded_values
    }


def exclude_by_name(
    dumped_model: dict[str, Any], *excluded_fields: str
) -> dict[str, Any]:
    """Strip all key-value pairs with certain field names.

    :param dumped_model: Dumped model
    :param excluded_fields: Excluded field names
    :return: Dumped model without excluded fields
    """
    return {
        field_name: field_value
        for field_name, field_value in dumped_model.items()
        if field_name not in excluded_fields
    }


def exclude_defaults(model: BaseModel, dumped_model: dict[str, Any]) -> dict[str, str]:
    """Strip all key-value pairs with default values.

    :param model: Model
    :param dumped_model: Dumped model
    :return: Dumped model without defaults
    """
    default_fields = {
        field_name: field_info.default
        for field_name, field_info in model.model_fields.items()
    }
    return {
        field_name: field_value
        for field_name, field_value in dumped_model.items()
        if field_value
        not in (
            default_fields.get(field_name),
            default_fields.get(to_snake(field_name)),
        )
    }


class CamelCaseConfigModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class DescConfigModel(BaseModel):
    @staticmethod
    def json_schema_extra(schema: dict[str, Any], model: type[BaseModel]) -> None:
        schema["description"] = describe_object(model.__doc__)

    model_config = ConfigDict(json_schema_extra=json_schema_extra)
