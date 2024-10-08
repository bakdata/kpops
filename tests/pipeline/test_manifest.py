from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
import yaml
from pytest_mock import MockerFixture
from pytest_snapshot.plugin import Snapshot
from typer.testing import CliRunner

import kpops.api as kpops
from kpops.cli.main import app
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmConfig, Version
from kpops.const.file_type import PIPELINE_YAML

MANIFEST_YAML = "manifest.yaml"

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache", "custom_components")
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

    def test_manifest_command(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "manifest",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_python_api(self, snapshot: Snapshot):
        resources = kpops.manifest(
            RESOURCE_PATH / "custom-config/pipeline.yaml",
            environment="development",
        )
        assert isinstance(resources, list)
        assert len(resources) == 2
        snapshot.assert_match(yaml.dump_all(resources), "resources")

    def test_streams_bootstrap(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "manifest",
                str(RESOURCE_PATH / "streams-bootstrap" / PIPELINE_YAML),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)
