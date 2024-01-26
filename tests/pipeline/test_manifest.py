from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from pytest_mock import MockerFixture
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

import kpops
from kpops.cli.main import app
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmConfig, Version

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


class TestManifest:
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

    def test_default_config(self, mock_execute: MagicMock):
        result = runner.invoke(
            app,
            [
                "manifest",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--environment",
                "development",
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
        assert result.exit_code == 0, result.stdout

    def test_custom_config(self, mock_execute: MagicMock):
        result = runner.invoke(
            app,
            [
                "manifest",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
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
        assert result.exit_code == 0, result.stdout

    def test_python_api(self, snapshot: SnapshotTest):
        resources = kpops.manifest(
            RESOURCE_PATH / "custom-config/pipeline.yaml",
            defaults=RESOURCE_PATH / "no-topics-defaults",
            output=False,
            environment="development",
        )
        assert isinstance(resources, list)
        assert len(resources) == 2
        for i, resource in enumerate(resources):
            snapshot.assert_match(resource, f"resource {i}")
