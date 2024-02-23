import json
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from hooks.gen_docs.gen_docs_env_vars import collect_fields
from kpops.config import KpopsConfig
from kpops.utils.docstring import describe_object

log = logging.getLogger("cli_commands_utils")


def is_jsonable(x):
    try:
        json.dumps(x)
    except (TypeError, OverflowError):
        return False
    else:
        return True


def touch_yaml_file(file_name, dir_path) -> Path:
    file_path = Path(dir_path / (file_name + ".yaml"))
    file_path.touch(exist_ok=False)
    return file_path


def extract_config_fields_for_yaml(
    fields: dict[str, Any], required: bool
) -> dict[str, Any]:
    extracted_fields = {}
    for key, value in fields.items():
        if issubclass(type(value), FieldInfo):
            if required and value.default in [PydanticUndefined, Ellipsis]:
                extracted_fields[key] = None
            elif not (required or value.default in [PydanticUndefined, Ellipsis]):
                if is_jsonable(value.default):
                    extracted_fields[key] = value.default
                else:
                    extracted_fields[key] = str(value.default)
        else:
            extracted_fields[key] = extract_config_fields_for_yaml(
                fields[key], required
            )
    return extracted_fields


def create_config(file_name: str, dir_path: Path) -> None:
    file_path = touch_yaml_file(file_name, dir_path)
    with file_path.open(mode="w") as conf:
        conf.write("# " + describe_object(KpopsConfig.__doc__))  # Write title
        non_required = extract_config_fields_for_yaml(
            collect_fields(KpopsConfig), False
        )
        required = extract_config_fields_for_yaml(collect_fields(KpopsConfig), True)
        for k in non_required:
            required.pop(k, None)
        conf.write("\n\n# Required fields\n")
        conf.write(yaml.dump(required))
        conf.write("\n# Non-required fields\n")
        conf.write(yaml.dump(non_required))


def init_project(path: Path):
    create_config("config", path)
    touch_yaml_file("pipeline", path)
    touch_yaml_file("defaults", path)
