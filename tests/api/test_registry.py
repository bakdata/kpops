from __future__ import annotations

import pytest

from kpops.api.exception import ClassNotFoundError
from kpops.api.registry import Registry, _find_classes, find_class
from kpops.component_handlers.schema_handler.schema_provider import SchemaProvider
from kpops.components.base_components.pipeline_component import PipelineComponent
from tests.cli.resources.custom_module import CustomSchemaProvider


class SubComponent(PipelineComponent): ...


class SubSubComponent(SubComponent): ...


class Unrelated:
    pass


@pytest.mark.skip()
def test_find_classes():
    gen = _find_classes(PipelineComponent)
    assert next(gen) is SubComponent
    assert next(gen) is SubSubComponent
    with pytest.raises(StopIteration):
        next(gen)


@pytest.mark.skip()
def test_find_builtin_classes():
    components = [class_.__name__ for class_ in _find_classes(PipelineComponent)]
    assert len(components) == 10
    assert components == [
        "HelmApp",
        "KafkaApp",
        "KafkaConnector",
        "KafkaSinkConnector",
        "KafkaSourceConnector",
        "KubernetesApp",
        "PipelineComponent",
        "ProducerApp",
        "StreamsApp",
        "StreamsBootstrap",
    ]


@pytest.mark.skip()
def test_find_class():
    assert find_class(SubComponent) is SubComponent
    assert find_class(PipelineComponent) is SubComponent
    assert find_class(SchemaProvider) is CustomSchemaProvider
    with pytest.raises(ClassNotFoundError):
        find_class(dict)


@pytest.mark.skip()
def test_registry():
    registry = Registry()
    assert registry._classes == {}
    registry.find_components()
    assert registry._classes == {
        "sub-component": SubComponent,
        "sub-sub-component": SubSubComponent,
    }
    assert registry["sub-component"] is SubComponent
    assert registry["sub-sub-component"] is SubSubComponent
    with pytest.raises(ClassNotFoundError):
        registry["doesnt-exist"]
