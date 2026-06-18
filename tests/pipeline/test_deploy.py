from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components import HelmApp
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache", "clear_kpops_config")
class TestDeploy:
    @pytest.fixture(autouse=True)
    def mock_helm(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.Helm",
            return_value=AsyncMock(),
        ).return_value

    def test_order(self, mocker: MockerFixture):
        producer_app_mock_deploy = mocker.patch.object(ProducerApp, "deploy")
        streams_app_mock_deploy = mocker.patch.object(StreamsApp, "deploy")
        helm_app_mock_deploy = mocker.patch.object(HelmApp, "deploy")
        mock_deploy = mocker.AsyncMock()
        mock_deploy.attach_mock(producer_app_mock_deploy, "producer_app_mock_deploy")
        mock_deploy.attach_mock(streams_app_mock_deploy, "streams_app_mock_deploy")
        mock_deploy.attach_mock(helm_app_mock_deploy, "helm_app_mock_deploy")

        result = runner.invoke(
            app,
            [
                "deploy",
                str(RESOURCE_PATH / "simple-pipeline" / "pipeline.yaml"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

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
