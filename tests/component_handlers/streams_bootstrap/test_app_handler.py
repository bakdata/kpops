from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.model import HelmConfig
from kpops.component_handlers.streams_bootstrap.handler import (
    AppHandler,
    ApplicationType,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestKafkaAppDeployment:
    @pytest.fixture(autouse=True)
    def helm_wrapper_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.streams_bootstrap.handler.Helm"
        ).return_value

    @pytest.fixture(autouse=True)
    def helm_config(self) -> HelmConfig:
        return HelmConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://raw.githubusercontent.com/bakdata/streams-bootstrap/2.4.0/charts/",
        )

    def test_should_call_helm_repo_add_when_initializing_app_handler(
        self, helm_wrapper_mock, helm_config: HelmConfig
    ):
        AppHandler(helm_config=helm_config)
        helm_wrapper_mock.helm_repo_add.assert_called_once_with(
            helm_config.repository_name, helm_config.url, None, None
        )

    def test_should_call_helm_upgrade_install_for_streams_app(
        self, helm_wrapper_mock, helm_config: HelmConfig
    ):
        handler = AppHandler(helm_config=helm_config)
        handler.install_app(
            "test-release",
            ApplicationType.STREAMS_APP,
            "test-namespace",
            {"commandLine": "test"},
            False,
        )
        helm_wrapper_mock.helm_upgrade_install.assert_called_once_with(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app=ApplicationType.STREAMS_APP.value,
            dry_run=False,
            local_chart_path=None,
        )

    def test_should_call_helm_upgrade_install_for_producer_app(
        self, helm_wrapper_mock, helm_config: HelmConfig
    ):
        handler = AppHandler(helm_config=helm_config)
        handler.install_app(
            release_name="test-release",
            application_type=ApplicationType.PRODUCER_APP,
            namespace="test-namespace",
            values={"commandLine": "test"},
            dry_run=False,
        )
        helm_wrapper_mock.helm_upgrade_install.assert_called_once_with(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app=ApplicationType.PRODUCER_APP.value,
            dry_run=False,
            local_chart_path=None,
        )

    def test_should_call_run_command_method_when_helm_uninstall(
        self, helm_wrapper_mock, helm_config: HelmConfig
    ):
        handler = AppHandler(helm_config=helm_config)
        handler.uninstall_app(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
            suffix="",
        )
        helm_wrapper_mock.helm_uninstall.assert_called_once_with(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
            suffix="",
        )
