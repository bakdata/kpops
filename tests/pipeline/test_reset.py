from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache")
class TestReset:
    @pytest.fixture(autouse=True)
    def mock_helm(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.Helm",
            return_value=AsyncMock(),
        ).return_value

    def test_order(self, mocker: MockerFixture):
        producer_app_mock_reset = mocker.patch(
            "kpops.components.streams_bootstrap.producer.producer_app.ProducerApp.reset",
        )
        streams_app_mock_reset = mocker.patch(
            "kpops.components.streams_bootstrap.streams.streams_app.StreamsApp.reset",
        )
        helm_app_mock_reset = mocker.patch(
            "kpops.components.base_components.helm_app.HelmApp.reset",
        )
        mock_reset = mocker.AsyncMock()
        mock_reset.attach_mock(producer_app_mock_reset, "producer_app_mock_reset")
        mock_reset.attach_mock(streams_app_mock_reset, "streams_app_mock_reset")
        mock_reset.attach_mock(helm_app_mock_reset, "helm_app_mock_reset")

        result = runner.invoke(
            app,
            [
                "reset",
                str(RESOURCE_PATH / "simple-pipeline" / "pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        # check called
        producer_app_mock_reset.assert_called_once_with(True)
        streams_app_mock_reset.assert_called_once_with(True)
        helm_app_mock_reset.assert_called_once_with(True)

        # check reverse order
        assert mock_reset.mock_calls == [
            mocker.call.helm_app_mock_reset(True),
            mocker.call.streams_app_mock_reset(True),
            mocker.call.producer_app_mock_reset(True),
        ]
