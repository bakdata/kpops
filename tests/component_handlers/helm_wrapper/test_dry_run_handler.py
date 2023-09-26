from logging import Logger
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.dry_run_handler import DryRunHandler
from kpops.component_handlers.helm_wrapper.model import HelmTemplate

log = Logger("TestLogger")


class TestDryRunHandler:
    @pytest.fixture()
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.Helm",
        ).return_value

    @pytest.fixture()
    def helm_diff_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.HelmDiff",
        ).return_value

    def test_should_print_helm_diff_when_release_is_new(
        self,
        helm_mock: MagicMock,
        helm_diff_mock: MagicMock,
        mocker: MockerFixture,
        caplog: LogCaptureFixture,
    ):
        helm_mock.get_manifest.return_value = iter(())
        mock_load_manifest = mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.Helm.load_manifest",
            return_value=iter([HelmTemplate("path.yaml", {"a": 1})]),
        )
        log.addHandler(caplog.handler)

        dry_run_handler = DryRunHandler(helm_mock, helm_diff_mock, "test-namespace")
        dry_run_handler.print_helm_diff("A test stdout", "a-release-name", log)

        helm_mock.get_manifest.assert_called_once_with(
            "a-release-name",
            "test-namespace",
        )
        assert "Helm release a-release-name does not exist" in caplog.text
        mock_load_manifest.assert_called_once_with("A test stdout")

    def test_should_print_helm_diff_when_release_exists(
        self,
        helm_mock: MagicMock,
        helm_diff_mock: MagicMock,
        mocker: MockerFixture,
        caplog: LogCaptureFixture,
    ):
        helm_mock.get_manifest.return_value = iter(
            [HelmTemplate("path.yaml", {"a": 1})],
        )
        mock_load_manifest = mocker.patch(
            "kpops.component_handlers.helm_wrapper.dry_run_handler.Helm.load_manifest",
            return_value=iter([HelmTemplate("path.yaml", {"a": 1})]),
        )
        log.addHandler(caplog.handler)

        dry_run_handler = DryRunHandler(helm_mock, helm_diff_mock, "test-namespace")
        dry_run_handler.print_helm_diff("A test stdout", "a-release-name", log)

        helm_mock.get_manifest.assert_called_once_with(
            "a-release-name",
            "test-namespace",
        )
        assert "Helm release a-release-name already exists" in caplog.text
        mock_load_manifest.assert_called_once_with("A test stdout")
