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
class TestDestroy:
    @pytest.fixture(autouse=True)
    def mock_helm(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.Helm",
            return_value=AsyncMock(),
        ).return_value

    def test_order(self, mocker: MockerFixture):
        producer_app_mock_destroy = mocker.patch.object(ProducerApp, "destroy")
        streams_app_mock_destroy = mocker.patch.object(StreamsApp, "destroy")
        helm_app_mock_destroy = mocker.patch.object(HelmApp, "destroy")
        mock_destroy = mocker.AsyncMock()
        mock_destroy.attach_mock(producer_app_mock_destroy, "producer_app_mock_destroy")
        mock_destroy.attach_mock(streams_app_mock_destroy, "streams_app_mock_destroy")
        mock_destroy.attach_mock(helm_app_mock_destroy, "helm_app_mock_destroy")

        result = runner.invoke(
            app,
            [
                "destroy",
                str(RESOURCE_PATH / "simple-pipeline" / "pipeline.yaml"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

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
