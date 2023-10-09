from __future__ import annotations

import importlib
import inspect
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

from kpops import __name__
from kpops.cli.exception import ClassNotFoundError
from kpops.components.base_components.pipeline_component import PipelineComponent

if TYPE_CHECKING:
    from collections.abc import Iterator

KPOPS_MODULE = __name__ + "."

T = TypeVar("T")
ClassDict = dict[str, type[T]]  # type -> class

sys.path.append(str(Path.cwd()))


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


def _find_classes(module_name: str, baseclass: type[T]) -> Iterator[type[T]]:
    module = importlib.import_module(module_name)
    for _, _class in inspect.getmembers(module, inspect.isclass):
        if issubclass(_class, baseclass):
            # filter out internal kpops classes unless specifically requested
            if _class.__module__.startswith(
                KPOPS_MODULE
            ) and not module_name.startswith(KPOPS_MODULE):
                continue
            yield _class
