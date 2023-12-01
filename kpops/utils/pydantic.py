import logging
from pathlib import Path
from typing import Any

import humps
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_snake
from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource
from typing_extensions import TypeVar, override

from kpops.utils.dict_ops import update_nested_pair
from kpops.utils.docstring import describe_object
from kpops.utils.yaml_loading import load_yaml_file


def to_camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    return humps.camelize(s)


def to_dash(s: str) -> str:
    """Convert PascalCase to dash-case."""
    return humps.depascalize(s).lower().replace("_", "-")


def to_dot(s: str) -> str:
    """Convert snake_case to dot.notation."""
    return s.replace("_", ".")


def by_alias(model: BaseModel, field_name: str) -> str:
    """Return field alias if exists else field name.

    :param field_name: Name of the field to get alias of
    :param model: Model that owns the field
    """
    return model.model_fields.get(field_name, Field()).alias or field_name


_V = TypeVar("_V")


def exclude_by_value(
    dumped_model: dict[str, _V], *excluded_values: Any
) -> dict[str, _V]:
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
    dumped_model: dict[str, _V], *excluded_fields: str
) -> dict[str, _V]:
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


def exclude_defaults(model: BaseModel, dumped_model: dict[str, _V]) -> dict[str, _V]:
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


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Loads variables from a YAML file at the project's root."""

    log = logging.getLogger()

    path_to_settings = Path()
    settings_file_base_name = "config"
    environment: str | None = None

    def __init__(self, settings_cls):
        super().__init__(settings_cls)
        # Check if path to settings yaml definition is valid
        if not self.path_to_settings.exists():
            msg = f"Path to config directory {self.path_to_settings} does not exist."
            raise ValueError(msg)
        elif self.path_to_settings.is_file():
            msg = f"Path to config directory {self.path_to_settings} must point to a directory."
            raise ValueError(msg)
        default_settings = self.__load_settings(
            self.path_to_settings / f"{self.settings_file_base_name}.yaml"
        )
        env_settings = (
            self.__load_settings(
                self.path_to_settings
                / f"{self.settings_file_base_name}_{self.environment}.yaml"
            )
            if self.environment
            else {}
        )
        self.settings = update_nested_pair(env_settings, default_settings)
        self.settings["environment"] = self.environment

    @staticmethod
    def __load_settings(file: Path) -> dict:
        if file.exists() and isinstance((loaded_file := load_yaml_file(file)), dict):
            if loaded_file.get("environment") is not None:
                msg = "Environment must not be specified in config.yaml."
                raise ValueError(msg)
            return loaded_file
        return {}

    @override
    def get_field_value(
        self,
        field: FieldInfo,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        return self.settings.get(field_name), field_name, False

    @override
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    @override
    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field,
                field_name,
            )
            field_value = self.prepare_field_value(
                field_name,
                field,
                field_value,
                value_is_complex,
            )
            if field_value is not None:
                d[field_key] = field_value
        return d
