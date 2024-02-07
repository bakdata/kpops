from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache")
class TestDeploy:
    @pytest.fixture(autouse=True)
    def mock_helm(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.Helm",
            return_value=AsyncMock(),
        ).return_value

    def test_order(self, mocker: MockerFixture):
        producer_app_mock_deploy = mocker.patch(
            "kpops.components.streams_bootstrap.producer.producer_app.ProducerApp.deploy",
        )
        streams_app_mock_deploy = mocker.patch(
            "kpops.components.streams_bootstrap.streams.streams_app.StreamsApp.deploy",
        )
        helm_app_mock_deploy = mocker.patch(
            "kpops.components.base_components.helm_app.HelmApp.deploy",
        )
        mock_deploy = mocker.AsyncMock()
        mock_deploy.attach_mock(producer_app_mock_deploy, "producer_app_mock_deploy")
        mock_deploy.attach_mock(streams_app_mock_deploy, "streams_app_mock_deploy")
        mock_deploy.attach_mock(helm_app_mock_deploy, "helm_app_mock_deploy")

        result = runner.invoke(
            app,
            [
                "deploy",
                str(RESOURCE_PATH / "simple-pipeline" / "pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
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
