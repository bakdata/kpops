import inspect
from collections import deque
from pathlib import Path

from kpops.cli.registry import Registry
from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
    deduplicate,
    defaults_from_yaml,
    update_nested,
)


def find_defaults(
    component_type: str, defaults_file_path: Path, components_module: str | None = None
) -> dict:
    registry = Registry()
    if components_module:
        registry.find_components(components_module)
    registry.find_components("kpops.components")
    component_class = registry[component_type]
    classes = deque(inspect.getmro(component_class))
    classes.appendleft(component_class)
    result: dict = {}
    for base in deduplicate(classes):
        if issubclass(base, BaseDefaultsComponent):
            result = update_nested(
                result,
                defaults_from_yaml(defaults_file_path, base.get_component_type()),
            )
    return result
