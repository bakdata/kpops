import sys
from typing import Any

import pytest
from pydantic import ValidationError

from kpops.components.base_components import (
    ConsumesTopics,
    HelmApp,
    KafkaSourceConnector,
    ProducesTopics,
)
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.streams_bootstrap.base import StreamsBootstrap
from kpops.components.streams_bootstrap.consumer.consumer_app import (
    ConsumerApp,
    ConsumerAppCleaner,
)
from kpops.components.streams_bootstrap.consumer_producer.consumer_producer_app import (
    ConsumerProducerAppCleaner,
)
from kpops.components.streams_bootstrap.model import StreamsBootstrapValues
from kpops.components.streams_bootstrap.producer.model import (
    ProducerAppValues,
    ProducerConfig,
)
from kpops.components.streams_bootstrap.producer.producer_app import (
    ProducerApp,
    ProducerAppCleaner,
)
from kpops.components.streams_bootstrap.streams.streams_app import StreamsAppCleaner
from kpops.core.registry import Registry, _find_classes, find_class
from tests.components.test_kubernetes_app import DummyKubernetesApp

registry = Registry()
registry.discover_components()

EXPECTED_PARENTS: dict[str, tuple[str, ...]] = {
    "consumer-app": (
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    "consumer-producer-app": (
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    "helm-app": ("kubernetes-app", "pipeline-component", "base-defaults-component"),
    "kafka-app": ("pipeline-component", "base-defaults-component"),
    "kafka-connector": (
        "kafka-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    "kafka-sink-connector": (
        "kafka-connector",
        "kafka-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    "kafka-source-connector": (
        "kafka-connector",
        "kafka-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    "kubernetes-app": ("pipeline-component", "base-defaults-component"),
    "pipeline-component": ("base-defaults-component",),
    "producer-app": (
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    "streams-app": (
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    "streams-bootstrap": (
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
}

EXPECTED_CLEANER_PARENTS: dict[type[PipelineComponent], tuple[str, ...]] = {
    StreamsAppCleaner: (
        "streams-bootstrap-cleaner",
        "cleaner",
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    ProducerAppCleaner: (
        "streams-bootstrap-cleaner",
        "cleaner",
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    ConsumerAppCleaner: (
        "streams-bootstrap-cleaner",
        "cleaner",
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
    ConsumerProducerAppCleaner: (
        "streams-bootstrap-cleaner",
        "cleaner",
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    ),
}


@pytest.mark.parametrize("component_type", sorted(EXPECTED_PARENTS))
def test_parents(component_type: str) -> None:
    component = registry[component_type]
    assert (
        tuple(parent.type for parent in component.parents)
        == EXPECTED_PARENTS[component_type]
    )


def test_all_components_covered() -> None:
    assert {c.type for c in registry.components} == set(EXPECTED_PARENTS)


@pytest.mark.parametrize(
    ("cleaner", "expected_parents"),
    sorted(EXPECTED_CLEANER_PARENTS.items(), key=lambda item: item[0].__name__),
)
def test_cleaner_parents(
    cleaner: type[PipelineComponent], expected_parents: tuple[str, ...]
) -> None:
    assert tuple(parent.type for parent in cleaner.parents) == expected_parents


class CustomStreamsBootstrapApp[
    V: StreamsBootstrapValues[Any] = StreamsBootstrapValues
](StreamsBootstrap[V]):
    runs_on_spot: bool = False


class CustomProducerApp(ProducerApp, CustomStreamsBootstrapApp[ProducerAppValues]): ...


def test_custom_diamond_parents() -> None:
    assert tuple(parent.type for parent in CustomProducerApp.parents) == (
        "producer-app",
        "custom-streams-bootstrap-app",
        "streams-bootstrap",
        "kafka-app",
        "helm-app",
        "kubernetes-app",
        "pipeline-component",
        "base-defaults-component",
    )


def test_custom_diamond_not_registered_as_generic() -> None:
    module = sys.modules[__name__]
    classes = list(_find_classes([module], base=PipelineComponent))
    assert CustomProducerApp in classes
    assert CustomStreamsBootstrapApp in classes
    assert not any("[" in cls.__name__ for cls in classes)
    assert find_class([module], base=CustomProducerApp) is CustomProducerApp


def test_custom_diamond_values() -> None:
    component = CustomProducerApp(
        name="test",
        namespace="test-namespace",
        values=ProducerAppValues(image="registry/producer", kafka=ProducerConfig()),
        enrich=False,
        validate=False,
    )
    assert isinstance(component.values, ProducerAppValues)
    assert component.runs_on_spot is False


@pytest.mark.parametrize(
    ("component", "section"),
    [
        (HelmApp, "from"),
        (HelmApp, "to"),
        (DummyKubernetesApp, "from"),
        (DummyKubernetesApp, "to"),
        (ProducerApp, "from"),
        (KafkaSourceConnector, "from"),
        (ConsumerApp, "to"),
    ],
)
def test_unsupported_topic_section_is_rejected(
    component: type[PipelineComponent], section: str
) -> None:
    with pytest.raises(
        ValidationError,
        match=rf"does not support the `{section}` section",
    ):
        component(name="test", enrich=False, **{section: {"topics": {"topic": {}}}})


def test_capabilities_are_not_component_types() -> None:
    capabilities = {ConsumesTopics, ProducesTopics}
    registered = set(registry.components)
    assert not capabilities & registered
    assert len(registered) == 12
    for component in (*registered, *EXPECTED_CLEANER_PARENTS):
        assert not capabilities & set(component.parents)
