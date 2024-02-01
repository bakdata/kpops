import logging
from pathlib import Path
from typing import Any

import humps
from pydantic import BaseModel, ConfigDict, Field
from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource
from typing_extensions import TypeVar, override

from kpops.utils.dict_ops import update_nested_pair
from kpops.utils.docstring import describe_object
from kpops.utils.yaml import load_yaml_file


def to_camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    return humps.camelize(s)


def to_dash(s: str) -> str:
    """Convert PascalCase to dash-case."""
    return humps.depascalize(s).lower().replace("_", "-")


def to_snake(s: str) -> str:
    """Convert PascalCase to snake_case."""
    return humps.depascalize(s).lower()


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


def issubclass_patched(
    __cls: type, __class_or_tuple: type | tuple[type, ...] = BaseModel
) -> bool:
    """Pydantic breaks ``issubclass``.

    .. code-block:: python
        issubclass(set[str], set)  # True
        issubclass(BaseSettings, BaseModel)  # True
        issubclass(set[str], BaseModel)  # raises Exception

    :param cls: class to check
    :base: class(es) to check against, defaults to ``BaseModel``
    :return: Whether 'cls' is derived from another class or is the same class.
    """
    try:
        return issubclass(__cls, __class_or_tuple)
    except TypeError as e:
        if str(e) == "issubclass() arg 1 must be a class":
            return False
        raise


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

    config_dir = Path()
    config_file_base_name = "config"
    environment: str | None = None

    def __init__(self, settings_cls) -> None:
        super().__init__(settings_cls)
        default_config = self.load_config(
            self.config_dir / f"{self.config_file_base_name}.yaml"
        )
        env_config = (
            self.load_config(
                self.config_dir
                / f"{self.config_file_base_name}_{self.environment}.yaml"
            )
            if self.environment
            else {}
        )
        self.config = update_nested_pair(env_config, default_config)

    @staticmethod
    def load_config(file: Path) -> dict:
        """Load YAML file if it exists.

        :param file: Path to a ``config*.yaml``
        :return: Dict containing the config or empty dict if file doesn't exist
        """
        if file.exists() and isinstance((loaded_file := load_yaml_file(file)), dict):
            return loaded_file
        return {}

    @override
    def get_field_value(
        self,
        field: FieldInfo,
        field_name: str,
    ) -> tuple[Any, str, bool]:
        return self.config.get(field_name), field_name, False

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
