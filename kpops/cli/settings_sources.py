from pathlib import Path
from typing import Any

from pydantic.fields import FieldInfo
from pydantic_settings import PydanticBaseSettingsSource

from kpops.utils.yaml_loading import load_yaml_file


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Loads variables from a YAML file at the project's root."""

    path_to_config = Path("config.yaml")

    def get_field_value(
        self, field: FieldInfo, field_name: str, # noqa: 
    ) -> tuple[Any, str, bool]:
        if self.path_to_config.exists() and isinstance((file_content_yaml := load_yaml_file(self.path_to_config)), dict):
            field_value = file_content_yaml.get(field_name)
            return field_value, field_name, False
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        d: dict[str, Any] = {}

        for field_name, field in self.settings_cls.model_fields.items():
            field_value, field_key, value_is_complex = self.get_field_value(
                field, field_name,
            )
            field_value = self.prepare_field_value(
                field_name, field, field_value, value_is_complex,
            )
            if field_value is not None:
                d[field_key] = field_value

        return d
