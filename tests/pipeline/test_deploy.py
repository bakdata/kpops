import pytest
from pytest_mock import MockerFixture

from kpops.components.base_components import HelmApp
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp
from kpops.pipeline import Pipeline


@pytest.mark.usefixtures("mock_env", "config", "handlers")
class TestDeploy:
    async def test_order(self, pipeline: Pipeline, mocker: MockerFixture) -> None:
        producer_app_mock_deploy = mocker.patch.object(ProducerApp, "deploy")
        streams_app_mock_deploy = mocker.patch.object(StreamsApp, "deploy")
        helm_app_mock_deploy = mocker.patch.object(HelmApp, "deploy")
        mock_deploy = mocker.AsyncMock()
        mock_deploy.attach_mock(producer_app_mock_deploy, "producer_app_mock_deploy")
        mock_deploy.attach_mock(streams_app_mock_deploy, "streams_app_mock_deploy")
        mock_deploy.attach_mock(helm_app_mock_deploy, "helm_app_mock_deploy")

        await pipeline.deploy(dry_run=True)

        # check called
        producer_app_mock_deploy.assert_called_once_with(True)
        streams_app_mock_deploy.assert_called_once_with(True)
        helm_app_mock_deploy.assert_called_once_with(True)

        # check order
        assert mock_deploy.mock_calls == [
            mocker.call.producer_app_mock_deploy(True),
            mocker.call.streams_app_mock_deploy(True),
            mocker.call.helm_app_mock_deploy(True),
        ]
