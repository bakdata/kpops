from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
import sys
from collections.abc import Iterable
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

    def find_components(self) -> None:
        """Find all PipelineComponent subclasses in module.

        :param module_name: name of the python module.
        """
        custom_modules = self.iter_component_modules()
        for _class in _find_classes(custom_modules, base=PipelineComponent):
            self._classes[_class.type] = _class

    def __getitem__(self, component_type: str) -> type[PipelineComponent]:
        try:
            return self._classes[component_type]
        except KeyError as ke:
            msg = f"Could not find a component of type {component_type}"
            raise ClassNotFoundError(msg) from ke

    @staticmethod
    def iter_component_modules() -> Iterator[ModuleType]:
        import kpops.components

        for _, module_name, _ in _iter_namespace(kpops.components):
            yield import_module(module_name)


def find_class(modules: Iterable[ModuleType], base: type[T]) -> type[T]:
    try:
        return next(_find_classes(modules, base=base))
    except StopIteration as e:
        raise ClassNotFoundError from e


def import_module(module_name: str) -> ModuleType:
    module = importlib.import_module(module_name)
    # TODO: remove? unnecessary now
    if module.__file__ and not module_name.startswith(KPOPS_MODULE):
        file_path = Path(module.__file__)
        try:
            rel_path = file_path.relative_to(Path.cwd())
            log.debug(f"Picked up: {rel_path}")
        except ValueError:
            log.debug(f"Picked up: {file_path}")
    return module


def _find_classes(modules: Iterable[ModuleType], base: type[T]) -> Iterator[type[T]]:
    for module in modules:
        for _, _class in inspect.getmembers(module, inspect.isclass):
            if not __filter_internal_kpops_classes(
                _class.__module__, module.__name__
            ) and issubclass(_class, base):
                yield _class


def __filter_internal_kpops_classes(class_module: str, module_name: str) -> bool:
    # filter out internal kpops classes and components unless specifically requested
    return class_module.startswith(KPOPS_MODULE) and not module_name.startswith(
        KPOPS_MODULE
    )


def _iter_namespace(ns_pkg: ModuleType) -> Iterator[pkgutil.ModuleInfo]:
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")
