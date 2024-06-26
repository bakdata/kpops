from __future__ import annotations

import importlib
import importlib.util
import inspect
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, TypeVar

from kpops import __name__
from kpops.api.exception import ClassNotFoundError
from kpops.components.base_components.pipeline_component import PipelineComponent

if TYPE_CHECKING:
    from collections.abc import Iterator

KPOPS_MODULE = __name__ + "."

T = TypeVar("T")
ClassDict = dict[str, type[T]]  # type -> class

sys.path.append(str(Path.cwd()))
log = logging.getLogger("Registry")


@dataclass
class Registry:
    """Class Registry to store and retrieve PipelineComponents."""

    _classes: ClassDict[PipelineComponent] = field(default_factory=dict, init=False)

    def find_components(self, module_name: str) -> None:
        """Find all PipelineComponent subclasses in module.

        :param module_name: name of the python module.
        """
        for _class in _find_classes(module_name, PipelineComponent):
            self._classes[_class.type] = _class

    def __getitem__(self, component_type: str) -> type[PipelineComponent]:
        try:
            return self._classes[component_type]
        except KeyError as ke:
            msg = f"Could not find a component of type {component_type}"
            raise ClassNotFoundError(msg) from ke


def find_class(module_name: str, baseclass: type[T]) -> type[T]:
    try:
        return next(_find_classes(module_name, baseclass))
    except StopIteration as e:
        raise ClassNotFoundError from e


def _import_module(module_name: str) -> ModuleType:
    module = importlib.import_module(module_name)
    if module.__file__ and not module_name.startswith(KPOPS_MODULE):
        file_path = Path(module.__file__)
        try:
            rel_path = file_path.relative_to(Path.cwd())
            log.debug(f"Picked up: {rel_path}")
        except ValueError:
            log.debug(f"Picked up: {file_path}")
    return module


def _find_classes(module_name: str, baseclass: type[T]) -> Iterator[type[T]]:
    module = _import_module(module_name)
    for _, _class in inspect.getmembers(module, inspect.isclass):
        if not __filter_internal_kpops_classes(
            _class.__module__, module_name
        ) and issubclass(_class, baseclass):
            yield _class


def __filter_internal_kpops_classes(class_module: str, module_name: str) -> bool:
    """Filter out internal KPOps classes and components unless specifically requested."""
    return class_module.startswith(KPOPS_MODULE) and not module_name.startswith(
        KPOPS_MODULE
    )


def _find_modules(path: Path) -> Iterator[str]:
    def python_file_to_module(py_file: Path) -> str:
        if py_file.suffix != ".py":
            msg = "Provided custom component path is not a Python file or directory"
            raise ValueError(msg)
        return py_file.with_suffix("").as_posix().replace("/", ".")

    if path.is_file():
        yield python_file_to_module(path)
    elif path.is_dir():
        for py_file in path.rglob("*.py"):
            yield python_file_to_module(py_file)
    else:
        msg = "Provide the path to a valid Python file or package"
        raise ValueError(msg)
