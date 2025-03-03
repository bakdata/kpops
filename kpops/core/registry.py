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

import typer

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.const import KPOPS_MODULE
from kpops.core.exception import ClassNotFoundError

if TYPE_CHECKING:
    from collections.abc import Iterator


_PluginT = TypeVar("_PluginT")
ClassDict = dict[str, type[_PluginT]]  # type -> class

sys.path.append(str(Path.cwd()))
log = logging.getLogger("Registry")


@dataclass
class Registry:
    """Class Registry to store and retrieve PipelineComponents."""

    _classes: ClassDict[PipelineComponent] = field(default_factory=dict, init=False)

    @property
    def components(self) -> Iterator[type[PipelineComponent]]:
        yield from self._classes.values()

    def discover_components(self) -> None:
        """Discover first- and third-party KPOps components.

        That is all classes inheriting from PipelineComponent.
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

        yield kpops.components
        yield from _iter_namespace(kpops.components)


def find_class(modules: Iterable[ModuleType], base: type[_PluginT]) -> type[_PluginT]:
    try:
        return next(_find_classes(modules, base=base))
    except StopIteration as e:
        raise ClassNotFoundError from e


def import_module(module_name: str) -> ModuleType:
    module = importlib.import_module(module_name)
    if module.__file__:
        log.debug(
            f"Loading {typer.style(module.__name__, bold=True)} ({module.__file__})"
        )
    return module


def _find_classes(
    modules: Iterable[ModuleType], base: type[_PluginT]
) -> Iterator[type[_PluginT]]:
    for module in modules:
        for _, _class in inspect.getmembers(module, inspect.isclass):
            if not __filter_internal_kpops_classes(
                _class.__module__, module.__name__
            ) and issubclass(_class, base):
                yield _class


def __filter_internal_kpops_classes(class_module: str, module_name: str) -> bool:
    """Filter out internal kpops classes and components unless specifically requested."""
    return class_module.startswith(KPOPS_MODULE) and not module_name.startswith(
        KPOPS_MODULE
    )


def _iter_namespace(ns_pkg: ModuleType) -> Iterator[ModuleType]:
    for _, module_name, _ in pkgutil.iter_modules(
        ns_pkg.__path__, ns_pkg.__name__ + "."
    ):
        yield import_module(module_name)
