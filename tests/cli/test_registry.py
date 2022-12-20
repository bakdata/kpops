from __future__ import annotations

import pytest
from pydantic import BaseModel

from kpops.cli.registry import ClassNotFoundError, Registry, _find_classes, find_class
from kpops.components.base_components.pipeline_component import PipelineComponent


class SubComponent(PipelineComponent):
    _type: str = "sub_component"
    pass


class SubSubComponent(SubComponent):
    _type: str = "sub_sub_component"
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
        SubComponent._type: SubComponent,
        SubSubComponent._type: SubSubComponent,
    }
    assert registry[SubComponent._type] == SubComponent
    assert registry[SubSubComponent._type] == SubSubComponent
    with pytest.raises(ClassNotFoundError):
        registry["doesnt-exist"]
