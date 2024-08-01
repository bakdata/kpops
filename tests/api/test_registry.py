from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

import pytest

from kpops.api.exception import ClassNotFoundError
from kpops.api.registry import Registry, _find_classes, _iter_namespace, find_class
from kpops.component_handlers.schema_handler.schema_provider import SchemaProvider
from kpops.components.base_components.helm_app import HelmApp
from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.base_components.kafka_connector import (
    KafkaConnector,
    KafkaSinkConnector,
    KafkaSourceConnector,
)
from kpops.components.base_components.kubernetes_app import KubernetesApp
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.common.streams_bootstrap import StreamsBootstrap
from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp
from kpops.components.streams_bootstrap_v3 import ProducerAppV3, StreamsAppV3
from tests.cli.resources.custom_module import CustomSchemaProvider


class SubComponent(PipelineComponent): ...


class SubSubComponent(SubComponent): ...


class Unrelated:
    pass


MODULE = SubComponent.__module__


def test_namespace():
    """Ensure namespace package according to PEP 420."""
    assert not Path("kpops/__init__.py").exists()
    assert not Path("kpops/components/__init__.py").exists()


@pytest.mark.usefixtures("custom_components")
def test_iter_namespace():
    components_module = importlib.import_module("kpops.components")
    assert [module.__name__ for module in _iter_namespace(components_module)] == [
        "kpops.components.base_components",
        "kpops.components.common",
        "kpops.components.streams_bootstrap",
        "kpops.components.streams_bootstrap_v3",
        "kpops.components.test_components",
    ]


@pytest.mark.usefixtures("custom_components")
def test_iter_component_modules():
    assert [module.__name__ for module in Registry.iter_component_modules()] == [
        "kpops.components",
        "kpops.components.base_components",
        "kpops.components.common",
        "kpops.components.streams_bootstrap",
        "kpops.components.streams_bootstrap_v3",
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


def test_find_class(module: ModuleType):
    assert find_class([module], base=SubComponent) is SubComponent
    assert find_class([module], base=PipelineComponent) is SubComponent
    assert find_class([module], base=SchemaProvider) is CustomSchemaProvider
    with pytest.raises(ClassNotFoundError):
        find_class([module], base=dict)


def test_registry():
    registry = Registry()
    assert registry._classes == {}
    registry.discover_components()
    assert registry._classes == {
        "helm-app": HelmApp,
        "kafka-app": KafkaApp,
        "kafka-connector": KafkaConnector,
        "kafka-sink-connector": KafkaSinkConnector,
        "kafka-source-connector": KafkaSourceConnector,
        "kubernetes-app": KubernetesApp,
        "pipeline-component": PipelineComponent,
        "producer-app": ProducerApp,
        "producer-app-v3": ProducerAppV3,
        "streams-app": StreamsApp,
        "streams-app-v3": StreamsAppV3,
        "streams-bootstrap": StreamsBootstrap,
    }
    for _type, _class in registry._classes.items():
        assert registry[_type] is _class
    with pytest.raises(ClassNotFoundError):
        registry["doesnt-exist"]
