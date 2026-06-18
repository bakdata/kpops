from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from kpops.config import KpopsConfig
from kpops.const.file_type import KpopsFileType
from kpops.utils.docstring import describe_object
from kpops.utils.json import is_jsonable
from kpops.utils.pydantic import collect_fields, issubclass_patched


def extract_config_fields_for_yaml(
    fields: dict[str, Any], required: bool
) -> dict[str, Any]:
    """Return only (non-)required fields and their respective default values.

    :param fields: Dict containing the fields to be categorized. The key of a
        record is the name of the field, the value is the field's type.
    :param required: Whether to extract only the required fields or only the
        non-required ones.
    """
    extracted_fields = {}
    for key, value in fields.items():
        if issubclass(type(value), FieldInfo):
            if required and value.default in [PydanticUndefined, Ellipsis]:
                extracted_fields[key] = None
            elif not (required or value.default in [PydanticUndefined, Ellipsis]):
                if is_jsonable(value.default):
                    extracted_fields[key] = value.default
                elif issubclass_patched(value.default, BaseModel):
                    extracted_fields[key] = value.default.model_dump(mode="json")
                else:
                    extracted_fields[key] = str(value.default)
        else:
            extracted_fields[key] = extract_config_fields_for_yaml(
                fields[key], required
            )
    return extracted_fields


def create_config(file_name: str, dir_path: Path, include_optional: bool) -> None:
    """Create a KPOps config yaml.

    :param file_name: Name for the file
    :param dir_path: Directory in which the file should be created
    :param include_optional: Whether to include non-required settings
    """
    file_path = Path(dir_path / (file_name + ".yaml"))
    file_path.touch(exist_ok=False)
    with file_path.open(mode="w") as conf:
        conf.write(f"# {describe_object(KpopsConfig.__doc__)}")  # Write title
        non_required = extract_config_fields_for_yaml(
            collect_fields(KpopsConfig), False
        )
        required = extract_config_fields_for_yaml(collect_fields(KpopsConfig), True)
        for k in non_required:
            required.pop(k, None)
        conf.write("\n\n# Required fields\n")
        conf.write(yaml.safe_dump(required))

        if include_optional:
            dump = KpopsConfig.model_validate(non_required).model_dump(
                mode="json", exclude_none=False
            )
            for k in required:
                dump.pop(k, None)
            conf.write("\n# Non-required fields\n")
            conf.write(yaml.safe_dump(dump))


def init_project(path: Path, conf_incl_opt: bool):
    """Initiate a default empty project.

    :param path: Directory in which the project should be initiated
    :param conf_incl_opt: Whether to include non-required settings
        in the generated config file
    """
    create_config(KpopsFileType.CONFIG.value, path, conf_incl_opt)
    Path(path / KpopsFileType.PIPELINE.as_yaml_file()).touch(exist_ok=False)
    Path(path / KpopsFileType.DEFAULTS.as_yaml_file()).touch(exist_ok=False)
