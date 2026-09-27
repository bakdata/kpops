import pytest
from pytest_mock import MockerFixture

from kpops.components.base_components import HelmApp
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp
from kpops.pipeline import Pipeline


@pytest.mark.usefixtures("mock_env", "config", "handlers")
class TestDestroy:
    async def test_order(self, pipeline: Pipeline, mocker: MockerFixture) -> None:
        producer_app_mock_destroy = mocker.patch.object(ProducerApp, "destroy")
        streams_app_mock_destroy = mocker.patch.object(StreamsApp, "destroy")
        helm_app_mock_destroy = mocker.patch.object(HelmApp, "destroy")
        mock_destroy = mocker.AsyncMock()
        mock_destroy.attach_mock(producer_app_mock_destroy, "producer_app_mock_destroy")
        mock_destroy.attach_mock(streams_app_mock_destroy, "streams_app_mock_destroy")
        mock_destroy.attach_mock(helm_app_mock_destroy, "helm_app_mock_destroy")

        await pipeline.destroy(dry_run=True)

        # check called
        producer_app_mock_destroy.assert_called_once_with(True)
        streams_app_mock_destroy.assert_called_once_with(True)
        helm_app_mock_destroy.assert_called_once_with(True)

        # check reverse order
        assert mock_destroy.mock_calls == [
            mocker.call.helm_app_mock_destroy(True),
            mocker.call.streams_app_mock_destroy(True),
            mocker.call.producer_app_mock_destroy(True),
        ]
