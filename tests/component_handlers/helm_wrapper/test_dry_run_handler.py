from logging import Logger
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.dry_run_handler import DryRunHandler
from kpops.component_handlers.helm_wrapper.model import HelmTemplate
from kpops.manifests.kubernetes import KubernetesManifest

log = Logger("TestLogger")


class TestDryRunHandler:
    @pytest.fixture()
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.Helm"
        ).return_value

    @pytest.fixture()
    def helm_diff_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.HelmDiff"
        ).return_value

    def test_should_print_helm_diff_when_release_is_new(
        self,
        helm_mock: MagicMock,
        helm_diff_mock: MagicMock,
        mocker: MockerFixture,
        caplog: LogCaptureFixture,
    ):
        helm_mock.get_manifest.return_value = iter(())
        new_release = iter(
            [
                HelmTemplate(
                    Path("path.yaml"),
                    KubernetesManifest.model_validate(
                        {"apiVersion": "v1", "kind": "Deployment", "metadata": {}}
                    ),
                )
            ]
        )
        mock_load_manifest = mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.Helm.load_manifest",
            return_value=new_release,
        )
        log.addHandler(caplog.handler)

        dry_run_handler = DryRunHandler(helm_mock, helm_diff_mock, "test-namespace")
        dry_run_handler.print_helm_diff("A test stdout", "a-release-name", log)

        helm_mock.get_manifest.assert_called_once_with(
            "a-release-name", "test-namespace"
        )
        assert "Helm release a-release-name does not exist" in caplog.text
        mock_load_manifest.assert_called_once_with("A test stdout")
        helm_diff_mock.log_helm_diff.assert_called_once_with(log, [], new_release)

    def test_should_print_helm_diff_when_release_exists(
        self,
        helm_mock: MagicMock,
        helm_diff_mock: MagicMock,
        mocker: MockerFixture,
        caplog: LogCaptureFixture,
    ):
        current_release = [
            HelmTemplate(
                Path("path.yaml"),
                KubernetesManifest.model_validate(
                    {"apiVersion": "v1", "kind": "Deployment", "metadata": {}}
                ),
            )
        ]

        helm_mock.get_manifest.return_value = iter(current_release)
        new_release = iter(
            [
                HelmTemplate(
                    Path("path.yaml"),
                    KubernetesManifest.model_validate(
                        {"apiVersion": "v1", "kind": "Deployment", "metadata": {}}
                    ),
                )
            ]
        )
        mock_load_manifest = mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.Helm.load_manifest",
            return_value=iter(new_release),
        )
        log.addHandler(caplog.handler)

        dry_run_handler = DryRunHandler(helm_mock, helm_diff_mock, "test-namespace")
        dry_run_handler.print_helm_diff("A test stdout", "a-release-name", log)

        helm_mock.get_manifest.assert_called_once_with(
            "a-release-name", "test-namespace"
        )
        assert "Helm release a-release-name already exists" in caplog.text
        mock_load_manifest.assert_called_once_with("A test stdout")
        helm_diff_mock.log_helm_diff.assert_called_once_with(
            log, current_release, new_release
        )
