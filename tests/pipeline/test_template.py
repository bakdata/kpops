from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.component_handlers.helm_wrapper.helm import Helm

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"
PIPELINE_BASE_DIR = str(RESOURCE_PATH.parent)


class TestTemplate:
    @pytest.fixture
    def run_command(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "_Helm__execute")

    def test_default_template_config(self, run_command: MagicMock):
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

        run_command.assert_called_with(
            [
                "helm",
                "template",
                "resources-custom-config-app2",
                "bakdata-streams-bootstrap/streams-app",
                "--values",
                ANY,
                "--version",
                "2.7.0",
            ],
        )

        assert result.exit_code == 0

    def test_template_config_with_flags(self, run_command: MagicMock):
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
                "--api-version",
                "2.1.1",
                "--ca-file",
                "ca-file",
                "--cert-file",
                "cert-file",
            ],
            catch_exceptions=False,
        )

        run_command.assert_called_with(
            [
                "helm",
                "template",
                "resources-custom-config-app2",
                "bakdata-streams-bootstrap/streams-app",
                "--values",
                ANY,
                "--api-versions",
                "2.1.1",
                "--ca-file",
                "ca-file",
                "--cert-file",
                "cert-file",
                "--version",
                "2.7.0",
            ],
        )

        assert result.exit_code == 0
