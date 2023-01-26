from __future__ import annotations

from typing import ClassVar, Literal

import pytest
from pydantic import BaseModel

from kpops.cli.registry import ClassNotFoundError, Registry, _find_classes, find_class
from kpops.components.base_components.pipeline_component import PipelineComponent


class SubComponent(PipelineComponent):
    type: ClassVar[Literal["sub-component"]] = "sub-component"
    pass


class SubSubComponent(SubComponent):
    type: ClassVar[Literal["sub-sub-component"]] = "sub-sub-component"
    pass


class Unrelated:
    pass


MODULE = SubComponent.__module__


def test_find_classes():
    gen = _find_classes(MODULE, BaseModel)
    assert next(gen) is SubComponent
    assert next(gen) is SubSubComponent
    with pytest.raises(StopIteration):
        next(gen)


def test_find_class():
    assert find_class(MODULE, SubComponent) is SubComponent
    assert find_class(MODULE, PipelineComponent) is SubComponent
    with pytest.raises(ClassNotFoundError):
        find_class(MODULE, dict)


def test_registry():
    registry = Registry()
    assert registry._classes == {}
    registry.find_components(MODULE)
    assert registry._classes == {
        "sub-component": SubComponent,
        "sub-sub-component": SubSubComponent,
    }
    assert registry["sub-component"] == SubComponent
    assert registry["sub-sub-component"] == SubSubComponent
    with pytest.raises(ClassNotFoundError):
        registry["doesnt-exist"]
