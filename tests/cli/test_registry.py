from __future__ import annotations

import pytest

from kpops.cli.registry import ClassNotFoundError, Registry, _find_classes, find_class
from kpops.component_handlers.schema_handler.schema_provider import SchemaProvider
from kpops.components.base_components.pipeline_component import PipelineComponent
from tests.cli.resources.module import CustomSchemaProvider


class SubComponent(PipelineComponent):
    type: str = "sub-component"


class SubSubComponent(SubComponent):
    type: str = "sub-sub-component"


class Unrelated:
    pass


MODULE = SubComponent.__module__


def test_find_classes():
    gen = _find_classes(MODULE, PipelineComponent)
    assert next(gen) is SubComponent
    assert next(gen) is SubSubComponent
    with pytest.raises(StopIteration):
        next(gen)


def test_find_builtin_classes():
    components = [
        class_.__name__
        for class_ in _find_classes("kpops.components", PipelineComponent)
    ]
    assert len(components) == 8
    assert components == [
        "KafkaApp",
        "KafkaConnector",
        "KafkaSinkConnector",
        "KafkaSourceConnector",
        "KubernetesApp",
        "PipelineComponent",
        "ProducerApp",
        "StreamsApp",
    ]


def test_find_class():
    assert find_class(MODULE, SubComponent) is SubComponent
    assert find_class(MODULE, PipelineComponent) is SubComponent
    assert find_class(MODULE, SchemaProvider) is CustomSchemaProvider
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
    assert registry["sub-component"] is SubComponent
    assert registry["sub-sub-component"] is SubSubComponent
    with pytest.raises(ClassNotFoundError):
        registry["doesnt-exist"]
