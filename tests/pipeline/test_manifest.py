from collections.abc import Iterator
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from _pytest.capture import CaptureFixture
from pytest_mock import MockerFixture
from pytest_snapshot.plugin import Snapshot
from typer.testing import CliRunner

import kpops.api as kpops
from kpops.cli.main import app
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmConfig, Version
from kpops.const.file_type import PIPELINE_YAML
from kpops.manifests.kubernetes import KubernetesManifest
from kpops.utils.yaml import print_yaml

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
    def mock_version(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(
            Helm,
            "version",
            return_value=Version(major=3, minor=12, patch=0),
            new_callable=mocker.PropertyMock,
        )

    @pytest.fixture(autouse=True)
    def helm(self, mock_version: MagicMock) -> Helm:
        return Helm(helm_config=HelmConfig())

    def test_default_config(self, mock_execute: MagicMock):
        result = runner.invoke(
            app,
            [
                "deploy",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--environment",
                "development",
                "--operation-mode",
                "manifest",
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
                "3.6.1",
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
                "deploy",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
                "--operation-mode",
                "manifest",
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
                "3.6.1",
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
                "deploy",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--environment",
                "development",
                "--operation-mode",
                "manifest",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_deploy_python_api(
        self, capsys: CaptureFixture[str], snapshot: Snapshot
    ):
        generator = kpops.manifest_deploy(
            RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML,
            environment="development",
        )
        assert isinstance(generator, Iterator)
        resources = list(generator)
        assert len(resources) == 2
        for resource in resources:
            for manifest in resource:
                assert isinstance(manifest, KubernetesManifest)
                print_yaml(manifest.model_dump())

        captured = capsys.readouterr()
        snapshot.assert_match(captured.out, MANIFEST_YAML)

    def test_streams_bootstrap(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "deploy",
                str(RESOURCE_PATH / "streams-bootstrap" / PIPELINE_YAML),
                "--operation-mode",
                "manifest",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_deploy_manifest_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "deploy",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "manifest",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_deploy_argo_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "deploy",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "argo",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_destroy_manifest_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "destroy",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "manifest",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_destroy_argo_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "destroy",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "argo",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_destroy_python_api(
        self, capsys: CaptureFixture[str], snapshot: Snapshot
    ):
        generator = kpops.manifest_destroy(
            RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML,
            environment="development",
        )
        assert isinstance(generator, Iterator)
        resources = list(generator)
        assert len(resources) == 2
        for resource in resources:
            for manifest in resource:
                assert isinstance(manifest, KubernetesManifest)
                print_yaml(manifest.model_dump())

        captured = capsys.readouterr()
        snapshot.assert_match(captured.out, MANIFEST_YAML)

    def test_manifest_reset_manifest_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "reset",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "manifest",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_reset_argo_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "reset",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "argo",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_reset_python_api(
        self, capsys: CaptureFixture[str], snapshot: Snapshot
    ):
        generator = kpops.manifest_reset(
            RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML,
            environment="development",
        )
        assert isinstance(generator, Iterator)
        resources = list(generator)
        assert len(resources) == 2
        for resource in resources:
            for manifest in resource:
                assert isinstance(manifest, KubernetesManifest)
                print_yaml(manifest.model_dump())

        captured = capsys.readouterr()
        snapshot.assert_match(captured.out, MANIFEST_YAML)

    def test_manifest_clean_manifest_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "clean",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "manifest",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_clean_argo_mode(self, snapshot: Snapshot):
        result = runner.invoke(
            app,
            [
                "clean",
                str(RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML),
                "--operation-mode",
                "argo",
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        snapshot.assert_match(result.stdout, MANIFEST_YAML)

    def test_manifest_clean_python_api(
        self, capsys: CaptureFixture[str], snapshot: Snapshot
    ):
        generator = kpops.manifest_clean(
            RESOURCE_PATH / "manifest-pipeline" / PIPELINE_YAML,
            environment="development",
        )
        assert isinstance(generator, Iterator)
        resources = list(generator)
        assert len(resources) == 2
        for resource in resources:
            for manifest in resource:
                assert isinstance(manifest, KubernetesManifest)
                print_yaml(manifest.model_dump())

        captured = capsys.readouterr()
        snapshot.assert_match(captured.out, MANIFEST_YAML)
