from enum import Enum
import logging
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

import yaml
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from hooks.gen_docs.gen_docs_env_vars import collect_fields
from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
)
from kpops.config import KpopsConfig
from kpops.utils.docstring import describe_object

from kpops.utils.gen_schema import _add_components

log = logging.getLogger("cli_commands_utils")



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
                extracted_fields[key] = str(value.default)
        else:
            extracted_fields[key] = extract_config_fields_for_yaml(
                fields[key], required
            )
    return extracted_fields


def get_subclasses(cls: type, include_self: bool):
    yield cls
    for _cls in cls.__subclasses__():
        yield from get_subclasses(_cls, True)

COMPONENT_TYPES = {
    cls.type: cls
    for cls
    in get_subclasses(BaseDefaultsComponent, False)
}

COMPONENT_TYPES_NO_ABC = {
    cls.type: cls
    for cls in _add_components("kpops.components", False)
}   

def generate_component_attrs(component: type[BaseDefaultsComponent], *exclude: str) -> Iterator[str]:
    for name, finfo in component.model_fields.items():
        if not (finfo.exclude or name in exclude):
            yield f"  {finfo.serialization_alias or name}:\n"  # TODO(Ivan Yordanov): Why that alias?

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


def create_defaults(
    file_name: str,
    dir_path: Path,
    components: Iterable[type[BaseDefaultsComponent]] | None,
) -> None:
    file_path = touch_yaml_file(file_name, dir_path)
    if components:
        bases = set()
        for component in components:
            for base in component.parents:
                bases.add(base)
    else:
        bases = set(COMPONENT_TYPES.values())
    with file_path.open(mode="w") as defaults:
        for component in bases:
            defaults.write(f"{component.type}:\n")
            defaults.writelines(generate_component_attrs(component))
            defaults.write("\n")


def create_pipeline(
    file_name: str,
    dir_path: Path,
    components: dict[str, type[BaseDefaultsComponent]] | None,
) -> None:
    file_path = touch_yaml_file(file_name, dir_path)
    with file_path.open(mode="w") as pipeline:
        for name, component in (components or COMPONENT_TYPES_NO_ABC).items():
            pipeline.write(f"- name: {name}\n")
            pipeline.write(f"  type: {component.type}\n")
            pipeline.writelines(generate_component_attrs(component, "name"))
            pipeline.write("\n")
