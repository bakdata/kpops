from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.helm.helm import Helm
from kpops.components.base_components import HelmApp
from kpops.components.base_components.helm_app import HelmAppValues
from kpops.components.streams_bootstrap.producer.model import ProducerAppValues
from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.model import StreamsAppValues
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp
from kpops.pipeline import Pipeline


@pytest.fixture()
def helm_mock(mocker: MockerFixture) -> MagicMock:
    helm_mock = mocker.MagicMock(Helm)
    mocker.patch(
        "kpops.components.base_components.helm_app.Helm", return_value=helm_mock
    )
    return helm_mock


@pytest.fixture()
def pipeline(helm_mock: MagicMock) -> Pipeline:
    pipeline = Pipeline(name="test-pipeline")
    pipeline.add(
        ProducerApp(
            name="producer",
            namespace="test-namespace",
            values=ProducerAppValues(image="producer-image"),
        )
    )
    pipeline.add(
        StreamsApp(
            name="streams",
            namespace="test-namespace",
            values=StreamsAppValues(image="streams-image"),
        )
    )
    pipeline.add(
        HelmApp(
            name="helm-app",
            namespace="test-namespace",
            values=HelmAppValues(),
        )
    )
    return pipeline
