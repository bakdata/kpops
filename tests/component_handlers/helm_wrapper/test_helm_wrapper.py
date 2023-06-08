from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.exception import ReleaseNotFoundException
from kpops.component_handlers.helm_wrapper.helm import Helm, HelmTemplate
from kpops.component_handlers.helm_wrapper.model import (
    HelmConfig,
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.components.streams_bootstrap.app_type import AppType

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestHelmWrapper:
    @pytest.fixture(autouse=True)
    def temp_file_mock(self, mocker: MockerFixture) -> MagicMock:
        temp_file_mock = mocker.patch("tempfile.NamedTemporaryFile")
        temp_file_mock.return_value.__enter__.return_value.name = "values.yaml"
        return temp_file_mock

    @pytest.fixture
    def run_command(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "_Helm__execute")

    @pytest.fixture
    def log_warning_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.helm_wrapper.helm.log.warning")

    def test_should_call_run_command_method_when_helm_install_with_defaults(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.upgrade_install(
            release_name="test-release",
            chart=f"bakdata-streams-bootstrap/{AppType.STREAMS_APP.value}",
            dry_run=False,
            namespace="test-namespace",
            values={"commandLine": "test"},
            flags=HelmUpgradeInstallFlags(),
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--install",
                "--timeout=5m0s",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--wait",
            ],
        )

    def test_should_include_configured_tls_parameters_on_add_when_version_is_old(
        self, run_command: MagicMock
    ):
        helm = Helm(HelmConfig())
        run_command.return_value = "v3.6.0+gc9f554d"

        helm.add_repo(
            "test-repository",
            "fake",
            RepoAuthFlags(ca_file=Path("a_file.ca"), insecure_skip_tls_verify=True),
        )
        assert run_command.mock_calls == [
            mock.call(
                [
                    "helm",
                    "repo",
                    "add",
                    "test-repository",
                    "fake",
                    "--ca-file",
                    "a_file.ca",
                    "--insecure-skip-tls-verify",
                ],
            ),
            mock.call(["helm", "version", "--short"]),
            mock.call(
                ["helm", "repo", "update"],
            ),
        ]

    def test_should_include_configured_tls_parameters_on_add_when_version_is_new(
        self, run_command: MagicMock
    ):
        helm = Helm(HelmConfig())
        run_command.return_value = "v3.12.0+gc9f554d"

        helm.add_repo(
            "test-repository",
            "fake",
            RepoAuthFlags(ca_file=Path("a_file.ca"), insecure_skip_tls_verify=True),
        )
        assert run_command.mock_calls == [
            mock.call(
                [
                    "helm",
                    "repo",
                    "add",
                    "test-repository",
                    "fake",
                    "--ca-file",
                    "a_file.ca",
                    "--insecure-skip-tls-verify",
                ],
            ),
            mock.call(["helm", "version", "--short"]),
            mock.call(
                ["helm", "repo", "update", "test-repository"],
            ),
        ]

    def test_should_include_configured_tls_parameters_on_update(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        helm_wrapper.upgrade_install(
            release_name="test-release",
            chart="test-repository/test-chart",
            dry_run=False,
            namespace="test-namespace",
            values={},
            flags=HelmUpgradeInstallFlags(
                repo_auth_flags=RepoAuthFlags(
                    ca_file=Path("a_file.ca"), insecure_skip_tls_verify=True
                )
            ),
        )

        run_command.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "test-repository/test-chart",
                "--install",
                "--timeout=5m0s",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--ca-file",
                "a_file.ca",
                "--insecure-skip-tls-verify",
                "--wait",
            ],
        )

    def test_should_call_run_command_method_when_helm_install_with_non_defaults(
        self,
        run_command: MagicMock,
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        helm_wrapper.upgrade_install(
            release_name="test-release",
            chart="test-repository/streams-app",
            namespace="test-namespace",
            dry_run=True,
            values={"commandLine": "test"},
            flags=HelmUpgradeInstallFlags(
                create_namespace=True,
                force=True,
                timeout="120s",
                wait=True,
                wait_for_jobs=True,
                version="2.4.2",
            ),
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "test-repository/streams-app",
                "--install",
                "--timeout=120s",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--create-namespace",
                "--dry-run",
                "--force",
                "--wait",
                "--wait-for-jobs",
                "--version",
                "2.4.2",
            ],
        )

    def test_should_call_run_command_method_when_uninstalling_streams_app(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        helm_wrapper.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
        )
        run_command.assert_called_once_with(
            ["helm", "uninstall", "test-release", "--namespace", "test-namespace"],
        )

    def test_should_log_warning_when_release_not_found(
        self, run_command: MagicMock, log_warning_mock: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        run_command.side_effect = ReleaseNotFoundException()
        helm_wrapper.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
        )

        log_warning_mock.assert_called_once_with(
            "Release with name test-release not found. Could not uninstall app."
        )

    def test_should_call_run_command_method_when_installing_streams_app__with_dry_run(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=True,
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "uninstall",
                "test-release",
                "--namespace",
                "test-namespace",
                "--dry-run",
            ],
        )

    def test_validate_console_output(self):
        with pytest.raises(RuntimeError):
            Helm.parse_helm_command_stderr_output(
                "A specific\n eRrOr was found in this line"
            )
        with pytest.raises(ReleaseNotFoundException):
            Helm.parse_helm_command_stderr_output("New \nmessage\n ReLease: noT foUnD")
        try:
            Helm.parse_helm_command_stderr_output("This is \njust WaRnIng nothing more")
        except RuntimeError as e:
            pytest.fail(
                f"validate_console_output() raised RuntimeError unexpectedly!\nError message: {e}"
            )
        try:
            Helm.parse_helm_command_stderr_output("This is \njust WaRnIng nothing more")
        except ReleaseNotFoundException:
            pytest.fail(
                f"validate_console_output() raised ReleaseNotFoundException unexpectedly!\nError message: {ReleaseNotFoundException}"
            )

    def test_load_manifest(self):
        stdout = """---
# Resource: chart/templates/test1.yaml
"""
        with pytest.raises(ValueError):
            helm_templates = list(Helm.load_manifest(stdout))
            assert len(helm_templates) == 0

        stdout = """---
# Source: chart/templates/test2.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
    labels:
        foo: bar
"""

        helm_template = HelmTemplate.load("test2.yaml", stdout)
        assert helm_template.filepath == "test2.yaml"
        assert helm_template.template == {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"labels": {"foo": "bar"}},
        }

        helm_templates = list(Helm.load_manifest(stdout))
        assert len(helm_templates) == 1
        helm_template = helm_templates[0]
        assert isinstance(helm_template, HelmTemplate)
        assert helm_template.filepath == "chart/templates/test2.yaml"
        assert helm_template.template == {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"labels": {"foo": "bar"}},
        }

        stdout = """---
# Source: chart/templates/test3a.yaml
data:
    - a: 1
    - b: 2
---
# Source: chart/templates/test3b.yaml
foo: bar
"""
        helm_templates = list(Helm.load_manifest(stdout))
        assert len(helm_templates) == 2
        assert all(
            isinstance(helm_template, HelmTemplate) for helm_template in helm_templates
        )
        assert helm_templates[0].filepath == "chart/templates/test3a.yaml"
        assert helm_templates[0].template == {"data": [{"a": 1}, {"b": 2}]}
        assert helm_templates[1].filepath == "chart/templates/test3b.yaml"
        assert helm_templates[1].template == {"foo": "bar"}

        stdout = """Release "test" has been upgraded. Happy Helming!
NAME: test
LAST DEPLOYED: Wed Nov 23 16:37:17 2022
NAMESPACE: test-namespace
STATUS: pending-upgrade
REVISION: 8
TEST SUITE: None
HOOKS:
MANIFEST:
---
# Source: chart/templates/test3a.yaml
data:
    - a: 1
    - b: 2
---
# Source: chart/templates/test3b.yaml
foo: bar

NOTES:
1. Get the application URL by running these commands:

    NOTES:

    test
"""
        helm_templates = list(Helm.load_manifest(stdout))
        assert len(helm_templates) == 2
        assert all(
            isinstance(helm_template, HelmTemplate) for helm_template in helm_templates
        )
        assert helm_templates[0].filepath == "chart/templates/test3a.yaml"
        assert helm_templates[0].template == {"data": [{"a": 1}, {"b": 2}]}
        assert helm_templates[1].filepath == "chart/templates/test3b.yaml"
        assert helm_templates[1].template == {"foo": "bar"}

    def test_get_manifest(self, run_command: MagicMock):
        helm_wrapper = Helm(helm_config=HelmConfig())
        run_command.return_value = """Release "test-release" has been upgraded. Happy Helming!
NAME: test-release
---
# Source: chart/templates/test.yaml
data:
    - a: 1
    - b: 2
"""
        helm_templates = list(
            helm_wrapper.get_manifest("test-release", "test-namespace")
        )
        run_command.assert_called_once_with(
            command=[
                "helm",
                "get",
                "manifest",
                "test-release",
                "--namespace",
                "test-namespace",
            ],
        )
        assert len(helm_templates) == 1
        assert helm_templates[0].filepath == "chart/templates/test.yaml"
        assert helm_templates[0].template == {"data": [{"a": 1}, {"b": 2}]}

        run_command.side_effect = ReleaseNotFoundException()
        assert helm_wrapper.get_manifest("test-release", "test-namespace") == ()

    def test_should_call_run_command_method_when_helm_template_with_optional_args(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.template(
            release_name="test-release",
            chart="bakdata-streams-bootstrap/streams-app",
            values={"commandLine": "test"},
            flags=HelmTemplateFlags(
                api_version="2.1.1",
                ca_file="a_file.ca",
                cert_file="a_file.pem",
            ),
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "template",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--values",
                "values.yaml",
                "--api-versions",
                "2.1.1",
                "--ca-file",
                "a_file.ca",
                "--cert-file",
                "a_file.pem",
            ],
        )

    def test_should_call_run_command_method_when_helm_template_without_optional_args(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.template(
            release_name="test-release",
            chart="bakdata-streams-bootstrap/streams-app",
            values={"commandLine": "test"},
            flags=HelmTemplateFlags(),
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "template",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--values",
                "values.yaml",
            ],
        )

    def test_should_get_helm_version(self, run_command: MagicMock):
        helm_wrapper = Helm(helm_config=HelmConfig())
        run_command.return_value = "v3.12.0+gc9f554d"

        version = helm_wrapper.get_version()

        run_command.assert_called_once_with(
            [
                "helm",
                "version",
                "--short",
            ],
        )

        assert version == "3.12.0"
