from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmConfig, Version

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"
PIPELINE_BASE_DIR = str(RESOURCE_PATH.parent)


class TestTemplate:
    @pytest.fixture()
    def mock_execute(self, mocker: MockerFixture) -> MagicMock:
        mock_execute = mocker.patch.object(Helm, "_Helm__execute")
        mock_execute.return_value = ""  # Helm Template
        return mock_execute

    @pytest.fixture()
    def mock_get_version(self, mocker: MockerFixture) -> MagicMock:
        mock_get_version = mocker.patch.object(Helm, "get_version")
        mock_get_version.return_value = Version(major=3, minor=12, patch=0)
        return mock_get_version

    @pytest.fixture(autouse=True)
    def helm(self, mock_get_version: MagicMock) -> Helm:
        return Helm(helm_config=HelmConfig())

    def test_default_template_config(self, mock_execute: MagicMock):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--template",
            ],
            catch_exceptions=False,
        )
        mock_execute.assert_called_with(
            [
                "helm",
                "template",
                "resources-custom-config-app2",
                "bakdata-streams-bootstrap/streams-app",
                "--namespace",
                "development-namespace",
                "--values",
                ANY,
                "--version",
                "2.9.0",
                "--timeout",
                "5m0s",
                "--wait",
            ],
        )
        assert result.exit_code == 0

    def test_template_config_with_flags(self, mock_execute: MagicMock):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--config",
                str(RESOURCE_PATH / "custom-config/config.yaml"),
                "--template",
            ],
            catch_exceptions=False,
        )
        mock_execute.assert_called_with(
            [
                "helm",
                "template",
                "resources-custom-config-app2",
                "bakdata-streams-bootstrap/streams-app",
                "--namespace",
                "development-namespace",
                "--values",
                ANY,
                "--version",
                "2.9.0",
                "--timeout",
                "5m0s",
                "--wait",
                "--api-versions",
                "2.1.1",
            ],
        )
        assert result.exit_code == 0
