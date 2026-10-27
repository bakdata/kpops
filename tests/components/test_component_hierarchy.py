import pytest

from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.streams_bootstrap.consumer.consumer_app import ConsumerAppCleaner
from kpops.components.streams_bootstrap.consumer_producer.consumer_producer_app import (
    ConsumerProducerAppCleaner,
)
from kpops.components.streams_bootstrap.producer.producer_app import ProducerAppCleaner
from kpops.components.streams_bootstrap.streams.streams_app import StreamsAppCleaner
from kpops.core.registry import Registry

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
    "kafka-connector": ("pipeline-component", "base-defaults-component"),
    "kafka-sink-connector": (
        "kafka-connector",
        "pipeline-component",
        "base-defaults-component",
    ),
    "kafka-source-connector": (
        "kafka-connector",
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
