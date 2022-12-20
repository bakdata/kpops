from __future__ import annotations

import importlib
import inspect
import os
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TypeVar

from kpops.cli.exception import ClassNotFoundError
from kpops.components.base_components.pipeline_component import PipelineComponent

T = TypeVar("T")
ClassDict = dict[str, type[T]]  # type -> class

sys.path.append(os.getcwd())


@dataclass
class Registry:
    """Class Registry to store and retrieve PipelineComponents."""

    _classes: ClassDict[PipelineComponent] = field(default_factory=dict, init=False)

    def find_components(self, module_name: str) -> None:
        """
        Find all PipelineComponent subclasses in module
        :param module_name: name of the python module
        """
        for _class in _find_classes(module_name, PipelineComponent):
            self._classes[_class._type] = _class

    def __getitem__(self, component_type: str) -> type[PipelineComponent]:
        try:
            return self._classes[component_type]
        except KeyError:
            raise ClassNotFoundError(
                f"Could not find a component of type {component_type}"
            )


def find_class(module_name: str, baseclass: type[T]) -> type[T]:
    try:
        return next(_find_classes(module_name, baseclass))
    except StopIteration:
        raise ClassNotFoundError


def _find_classes(module_name: str, baseclass: type[T]) -> Iterator[type[T]]:
    module = importlib.import_module(module_name)
    for _, _class in inspect.getmembers(module, inspect.isclass):
        if issubclass(_class, baseclass) and module_name in _class.__module__:
            yield _class
