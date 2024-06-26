from __future__ import annotations

import importlib
import shutil
from pathlib import Path
from types import ModuleType

import pytest
from pytest_mock import MockerFixture

from kpops.api.exception import ClassNotFoundError
from kpops.api.registry import Registry, _find_classes, _iter_namespace, find_class
from kpops.component_handlers.schema_handler.schema_provider import SchemaProvider
from kpops.components import (
    HelmApp,
    KafkaApp,
    KafkaConnector,
    KafkaSinkConnector,
    KafkaSourceConnector,
    KubernetesApp,
    PipelineComponent,
    ProducerApp,
    StreamsApp,
    StreamsBootstrap,
)
from tests.cli.resources.custom_module import CustomSchemaProvider


class SubComponent(PipelineComponent): ...


class SubSubComponent(SubComponent): ...


class Unrelated:
    pass


MODULE = SubComponent.__module__


@pytest.fixture()
def custom_components(mocker: MockerFixture):
    src = Path("tests/pipeline/test_components")
    dst = Path("kpops/components/test_components")
    try:
        shutil.copytree(src, dst)
        yield
    finally:
        shutil.rmtree(dst)


@pytest.mark.usefixtures("custom_components")
def test_iter_namespace():
    components_module = importlib.import_module("kpops.components")
    assert [
        module_name for _, module_name, _ in _iter_namespace(components_module)
    ] == [
        "kpops.components.base_components",
        "kpops.components.streams_bootstrap",
        "kpops.components.test_components",
    ]


@pytest.mark.usefixtures("custom_components")
def test_iter_component_modules():
    assert [module.__name__ for module in Registry.iter_component_modules()] == [
        "kpops.components.base_components",
        "kpops.components.streams_bootstrap",
        "kpops.components.test_components",
    ]


@pytest.fixture()
def module() -> ModuleType:
    return importlib.import_module(MODULE)


def test_find_classes(module: ModuleType):
    gen = _find_classes([module], PipelineComponent)
    assert next(gen) is SubComponent
    assert next(gen) is SubSubComponent
    with pytest.raises(StopIteration):
        next(gen)


def test_find_builtin_classes():
    modules = Registry.iter_component_modules()
    components = [
        class_.__name__ for class_ in _find_classes(modules, base=PipelineComponent)
    ]
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


def test_find_class(module: ModuleType):
    assert find_class([module], base=SubComponent) is SubComponent
    assert find_class([module], base=PipelineComponent) is SubComponent
    assert find_class([module], base=SchemaProvider) is CustomSchemaProvider
    with pytest.raises(ClassNotFoundError):
        find_class([module], base=dict)


def test_registry():
    registry = Registry()
    assert registry._classes == {}
    registry.find_components()
    assert registry._classes == {
        "helm-app": HelmApp,
        "kafka-app": KafkaApp,
        "kafka-connector": KafkaConnector,
        "kafka-sink-connector": KafkaSinkConnector,
        "kafka-source-connector": KafkaSourceConnector,
        "kubernetes-app": KubernetesApp,
        "pipeline-component": PipelineComponent,
        "producer-app": ProducerApp,
        "streams-app": StreamsApp,
        "streams-bootstrap": StreamsBootstrap,
    }
    for _type, _class in registry._classes.items():
        assert registry[_type] is _class
    with pytest.raises(ClassNotFoundError):
        registry["doesnt-exist"]
