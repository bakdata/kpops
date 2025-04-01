import os
from pathlib import Path
from textwrap import dedent
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.exception import (
    ParseError,
    ReleaseNotFoundException,
)
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import (
    HelmConfig,
    HelmTemplate,
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
    Version,
)
from kpops.components.common.app_type import AppType
from kpops.manifests.kubernetes import KubernetesManifest


class TestHelmWrapper:
    @pytest.fixture(autouse=True)
    def temp_file_mock(self, mocker: MockerFixture) -> MagicMock:
        temp_file_mock = mocker.patch("tempfile.NamedTemporaryFile")
        temp_file_mock.return_value.__enter__.return_value.name = "values.yaml"
        return temp_file_mock

    @pytest.fixture()
    def mock_execute(self, mocker: MockerFixture) -> MagicMock:
        mock_execute = mocker.patch.object(Helm, "_Helm__execute")
        mock_execute.return_value = ""
        return mock_execute

    @pytest.fixture()
    def run_command_async(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "_Helm__async_execute")

    @pytest.fixture()
    def log_warning_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.helm_wrapper.helm.log.warning")

    @pytest.fixture()
    def mock_version(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(
            Helm,
            "version",
            return_value=Version(major=3, minor=12, patch=0),
            new_callable=mocker.PropertyMock,
        )

    @pytest.fixture()
    def helm(self, mock_version: MagicMock) -> Helm:
        return Helm(helm_config=HelmConfig())

    @pytest.fixture(autouse=True)
    def cache_clear(self) -> None:
        helm = Helm._instance
        if not helm:
            return
        helm.add_repo.cache_clear()  # pyright: ignore[reportFunctionMemberAccess]
        if hasattr(helm, "version"):
            del helm.version

    def test_singleton(self, helm: Helm) -> None:
        assert Helm(helm_config=HelmConfig()) is helm

    def test_version_cached(self, helm: Helm, mock_execute: MagicMock):
        assert helm.version
        mock_execute.assert_not_called()

    def test_add_repo_cached(self, helm: Helm, mock_execute: MagicMock):
        helm.add_repo("test-foo", "fake")
        helm.add_repo("test-bar", "fake")
        helm.add_repo("test-foo", "fake")
        helm.add_repo("test-bar", "fake2")
        assert mock_execute.mock_calls == [
            mock.call(
                [
                    "helm",
                    "repo",
                    "add",
                    "test-foo",
                    "fake",
                ],
            ),
            mock.call(
                ["helm", "repo", "update", "test-foo"],
            ),
            mock.call(
                [
                    "helm",
                    "repo",
                    "add",
                    "test-bar",
                    "fake",
                ],
            ),
            mock.call(
                ["helm", "repo", "update", "test-bar"],
            ),
            mock.call(
                [
                    "helm",
                    "repo",
                    "add",
                    "test-bar",
                    "fake2",
                ],
            ),
            mock.call(
                ["helm", "repo", "update", "test-bar"],
            ),
        ]

    async def test_should_call_run_command_method_when_helm_install_with_defaults(
        self, helm: Helm, run_command_async: AsyncMock
    ):
        await helm.upgrade_install(
            release_name="test-release",
            chart=f"bakdata-streams-bootstrap/{AppType.STREAMS_APP.value}",
            dry_run=False,
            namespace="test-namespace",
            values={"commandLine": "test"},
            flags=HelmUpgradeInstallFlags(),
        )

        run_command_async.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--install",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--timeout",
                "5m0s",
                "--wait",
            ],
        )

    def test_should_include_configured_tls_parameters_on_add_when_version_is_old(
        self, mock_execute: MagicMock, mocker: MockerFixture
    ):
        mocker.patch.object(
            Helm,
            "version",
            return_value=Version(major=3, minor=6, patch=0),
            new_callable=mocker.PropertyMock,
        )
        helm = Helm(HelmConfig())

        helm.add_repo(
            "test-repository",
            "fake",
            RepoAuthFlags(ca_file=Path("a_file.ca"), insecure_skip_tls_verify=True),
        )
        assert mock_execute.mock_calls == [
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
            mock.call(
                ["helm", "repo", "update"],
            ),
        ]

    def test_should_include_configured_tls_parameters_on_add_when_version_is_new(
        self, helm: Helm, mock_execute: MagicMock
    ):
        helm.add_repo(
            "test-repository",
            "fake",
            RepoAuthFlags(ca_file=Path("a_file.ca"), insecure_skip_tls_verify=True),
        )
        assert mock_execute.mock_calls == [
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
            mock.call(
                ["helm", "repo", "update", "test-repository"],
            ),
        ]

    async def test_should_include_configured_tls_parameters_on_update(
        self, helm: Helm, run_command_async: AsyncMock
    ):
        await helm.upgrade_install(
            release_name="test-release",
            chart="test-repository/test-chart",
            dry_run=False,
            namespace="test-namespace",
            values={},
            flags=HelmUpgradeInstallFlags(
                ca_file=Path("a_file.ca"),
                insecure_skip_tls_verify=True,
            ),
        )

        run_command_async.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "test-repository/test-chart",
                "--install",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--ca-file",
                "a_file.ca",
                "--insecure-skip-tls-verify",
                "--timeout",
                "5m0s",
                "--wait",
            ],
        )

    async def test_should_call_run_command_method_when_helm_install_with_non_defaults(
        self, helm: Helm, run_command_async: AsyncMock
    ):
        await helm.upgrade_install(
            release_name="test-release",
            chart="test-repository/streams-app",
            namespace="test-namespace",
            dry_run=True,
            values={"commandLine": "test"},
            flags=HelmUpgradeInstallFlags(
                create_namespace=True,
                force=True,
                set_file={"key1": Path("example/path1"), "key2": Path("example/path2")},
                timeout="120s",
                wait=True,
                wait_for_jobs=True,
                version="2.4.2",
            ),
        )
        run_command_async.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "test-repository/streams-app",
                "--install",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--set-file",
                f"key1=example{os.path.sep}path1,key2=example{os.path.sep}path2",
                "--create-namespace",
                "--version",
                "2.4.2",
                "--force",
                "--timeout",
                "120s",
                "--wait",
                "--wait-for-jobs",
                "--dry-run",
            ],
        )

    async def test_should_call_run_command_method_when_uninstalling_streams_app(
        self, helm: Helm, run_command_async: AsyncMock
    ):
        await helm.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
        )
        run_command_async.assert_called_once_with(
            ["helm", "uninstall", "test-release", "--namespace", "test-namespace"],
        )

    async def test_should_log_warning_when_release_not_found(
        self,
        run_command_async: AsyncMock,
        helm: Helm,
        log_warning_mock: MagicMock,
    ):
        run_command_async.side_effect = ReleaseNotFoundException()
        await helm.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
        )

        log_warning_mock.assert_called_once_with(
            "Release with name test-release not found. Could not uninstall app."
        )

    async def test_should_call_run_command_method_when_installing_streams_app__with_dry_run(
        self, helm: Helm, run_command_async: AsyncMock
    ):
        await helm.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=True,
        )
        run_command_async.assert_called_once_with(
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

    def test_helm_template(self):
        path = Path("test2.yaml")
        manifest = KubernetesManifest.model_validate(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {"labels": {"foo": "bar"}},
            }
        )
        helm_template = HelmTemplate(path, manifest)
        assert helm_template.filepath == path
        assert helm_template.manifest == manifest

    def test_load_manifest_with_no_notes(self):
        stdout = dedent(
            """
            MANIFEST:
            ---
            # Source: chart/templates/test3a.yaml
            apiVersion: v1
            kind: Pod
            metadata:
              name: test-3a
            ---
            # Source: chart/templates/test3b.yaml
            apiVersion: v1
            kind: Pod
            metadata:
              name: test-3b
            """
        )
        helm_templates = list(Helm.load_manifest(stdout))
        assert len(helm_templates) == 2
        assert all(
            isinstance(helm_template, HelmTemplate) for helm_template in helm_templates
        )
        assert helm_templates[0].filepath == Path("chart/templates/test3a.yaml")
        assert helm_templates[0].manifest == KubernetesManifest.model_validate(
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {"name": "test-3a"},
            }
        )
        assert helm_templates[1].filepath == Path("chart/templates/test3b.yaml")
        assert helm_templates[1].manifest == KubernetesManifest.model_validate(
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {"name": "test-3b"},
            }
        )

    def test_raise_parse_error_when_helm_content_is_invalid(self):
        stdout = dedent(
            """
            ---
            # Resource: chart/templates/test1.yaml
            """
        )
        with pytest.raises(ParseError, match="Not a valid Helm template source"):
            list(Helm.load_manifest(stdout))

    def test_load_manifest(self):
        stdout = dedent(
            """
            Release "test" has been upgraded. Happy Helming!
            NAME: test
            LAST DEPLOYED: Wed Nov 23 16:37:17 2022
            NAMESPACE: test-namespace
            STATUS: pending-upgrade
            REVISION: 8
            TEST SUITE: None
            HOOKS:
            ---
            # Source: chart/templates/test/test-connection.yaml
            apiVersion: v1
            kind: Pod
            metadata:
              name: "random-test-connection"
              annotations:
                "helm.sh/hook": test
            spec:
              containers:
                - name: wget
                  image: busybox
                  command: ['wget']
                  args: ['random:80']
            ---
            # Source: chart/templates/test-hook.yaml
            apiVersion: batch/v1
              annotations:
                "helm.sh/hook": post-install
            MANIFEST:
            ---
            # Source: chart/templates/test3a.yaml
            apiVersion: v1
            kind: Pod
            metadata:
              name: test-3a
            ---
            # Source: chart/templates/test3b.yaml
            apiVersion: v1
            kind: Pod
            metadata:
              name: test-3b

            NOTES:
            1. Get the application URL by running these commands:

                NOTES:

                test
            """
        )
        helm_templates = list(Helm.load_manifest(stdout))
        assert len(helm_templates) == 2
        assert all(
            isinstance(helm_template, HelmTemplate) for helm_template in helm_templates
        )
        assert helm_templates[0].filepath == Path("chart/templates/test3a.yaml")
        assert helm_templates[0].manifest == KubernetesManifest.model_validate(
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {"name": "test-3a"},
            }
        )
        assert helm_templates[1].filepath == Path("chart/templates/test3b.yaml")
        assert helm_templates[1].manifest == KubernetesManifest.model_validate(
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {"name": "test-3b"},
            }
        )

    def test_helm_get_manifest(self, helm: Helm, mock_execute: MagicMock):
        mock_execute.return_value = dedent(
            """
            ---
            # Source: chart/templates/test.yaml
            apiVersion: v1
            kind: Pod
            metadata:
              name: my-pod
            """
        )
        helm_templates = list(helm.get_manifest("test-release", "test-namespace"))
        mock_execute.assert_called_once_with(
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
        assert helm_templates[0].filepath == Path("chart/templates/test.yaml")
        assert helm_templates[0].manifest == KubernetesManifest.model_validate(
            {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {"name": "my-pod"},
            }
        )

        mock_execute.side_effect = ReleaseNotFoundException()
        assert helm.get_manifest("test-release", "test-namespace") == ()

    def test_should_call_run_command_method_when_helm_template_with_optional_args(
        self, helm: Helm, mock_execute: MagicMock
    ):
        helm.template(
            release_name="test-release",
            chart="bakdata-streams-bootstrap/streams-app",
            namespace="test-ns",
            values={"commandLine": "test"},
            flags=HelmTemplateFlags(
                api_version="2.1.1",
                ca_file=Path("a_file.ca"),
                cert_file=Path("a_file.pem"),
            ),
        )
        mock_execute.assert_called_once_with(
            [
                "helm",
                "template",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--namespace",
                "test-ns",
                "--values",
                "values.yaml",
                "--ca-file",
                "a_file.ca",
                "--cert-file",
                "a_file.pem",
                "--timeout",
                "5m0s",
                "--wait",
                "--api-versions",
                "2.1.1",
            ],
        )

    def test_should_call_run_command_method_when_helm_template_without_optional_args(
        self, helm: Helm, mock_execute: MagicMock
    ):
        helm.template(
            release_name="test-release",
            chart="bakdata-streams-bootstrap/streams-app",
            namespace="test-ns",
            values={"commandLine": "test"},
        )
        mock_execute.assert_called_once_with(
            [
                "helm",
                "template",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--namespace",
                "test-ns",
                "--values",
                "values.yaml",
                "--timeout",
                "5m0s",
                "--wait",
            ],
        )

    @pytest.mark.parametrize(
        ("raw_version", "expected_version"),
        [
            ("v3.12.0+gc9f554d", Version(3, 12, 0)),
            ("v3.12.0", Version(3, 12, 0)),
            ("v3.12", Version(3, 12, 0)),
            ("v3", Version(3, 0, 0)),
        ],
    )
    def test_parse_version(
        self,
        mock_execute: MagicMock,
        raw_version: str,
        expected_version: Version,
    ):
        mock_execute.return_value = raw_version
        helm = Helm(helm_config=HelmConfig())

        mock_execute.assert_called_once_with(
            [
                "helm",
                "version",
                "--short",
            ],
        )
        assert helm.version == expected_version

    def test_should_raise_exception_if_helm_version_is_old(
        self, mock_execute: MagicMock
    ):
        mock_execute.return_value = "v2.9.0+gc9f554d"
        with pytest.raises(
            RuntimeError,
            match="The supported Helm version is 3.x.x. The current Helm version is 2.9.0",
        ):
            Helm(helm_config=HelmConfig())

    def test_should_raise_exception_if_helm_version_cannot_be_parsed(
        self, mock_execute: MagicMock
    ):
        mock_execute.return_value = "123"
        with pytest.raises(
            RuntimeError, match="Could not parse the Helm version.\n\nHelm output:\n123"
        ):
            Helm(helm_config=HelmConfig())
