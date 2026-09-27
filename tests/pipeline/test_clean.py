import pytest
from pytest_mock import MockerFixture

from kpops.components.base_components import HelmApp
from kpops.components.streams_bootstrap.producer.producer_app import (
    ProducerApp,
    ProducerAppCleaner,
)
from kpops.components.streams_bootstrap.streams.streams_app import (
    StreamsApp,
    StreamsAppCleaner,
)
from kpops.pipeline import Pipeline


@pytest.mark.usefixtures("mock_env", "config", "handlers")
class TestClean:
    async def test_order(self, pipeline: Pipeline, mocker: MockerFixture) -> None:
        # destroy
        producer_app_mock_destroy = mocker.patch.object(ProducerApp, "destroy")
        streams_app_mock_destroy = mocker.patch.object(StreamsApp, "destroy")
        helm_app_mock_destroy = mocker.patch.object(HelmApp, "destroy")

        # clean
        streams_app_mock_clean = mocker.patch.object(StreamsAppCleaner, "clean")
        producer_app_mock_clean = mocker.patch.object(ProducerAppCleaner, "clean")

        async_mocker = mocker.AsyncMock()
        async_mocker.attach_mock(producer_app_mock_destroy, "producer_app_mock_destroy")
        async_mocker.attach_mock(streams_app_mock_destroy, "streams_app_mock_destroy")
        async_mocker.attach_mock(helm_app_mock_destroy, "helm_app_mock_destroy")

        async_mocker.attach_mock(producer_app_mock_clean, "producer_app_mock_clean")
        async_mocker.attach_mock(streams_app_mock_clean, "streams_app_mock_clean")

        await pipeline.clean(dry_run=True)

        # check called
        producer_app_mock_destroy.assert_called_once_with(True)
        streams_app_mock_destroy.assert_called_once_with(True)
        helm_app_mock_destroy.assert_called_once_with(True)

        producer_app_mock_clean.assert_called_once_with(True)
        streams_app_mock_clean.assert_called_once_with(True)

        # check reverse order
        assert async_mocker.mock_calls == [
            # HelmApp
            mocker.call.helm_app_mock_destroy(True),
            # StreamsApp
            mocker.call.streams_app_mock_destroy(True),
            mocker.call.streams_app_mock_clean(True),
            # ProducerApp
            mocker.call.producer_app_mock_destroy(True),
            mocker.call.producer_app_mock_clean(True),
        ]
