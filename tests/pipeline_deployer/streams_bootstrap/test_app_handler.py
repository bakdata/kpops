import unittest
from pathlib import Path
from unittest.mock import patch

from kpops.pipeline_deployer.streams_bootstrap.handler import (
    AppHandler,
    ApplicationType,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestKafkaAppDeployment(unittest.TestCase):
    @patch("kpops.pipeline_deployer.streams_bootstrap.helm_wrapper")
    def test_should_call_helm_upgrade_install_for_streams_app(self, wrapper):
        handler = AppHandler(helm_wrapper=wrapper)
        handler.install_app(
            "test-release",
            "test-namespace",
            {"commandLine": "test"},
            ApplicationType.STREAMS_APP,
            False,
        )
        wrapper.helm_upgrade_install.assert_called_once_with(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app=ApplicationType.STREAMS_APP.value,
            dry_run=False,
            local_chart_path=None,
        )

    @patch("kpops.pipeline_deployer.streams_bootstrap.helm_wrapper")
    def test_should_call_helm_upgrade_install_for_streams_app_overriding_repo(
        self, wrapper
    ):
        handler = AppHandler(helm_wrapper=wrapper)
        handler.install_app(
            "test-release",
            "test-namespace",
            {"commandLine": "test"},
            ApplicationType.STREAMS_APP,
            False,
            local_chart_path=Path("my/fake/dir"),
        )
        wrapper.helm_upgrade_install.assert_called_once_with(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app=ApplicationType.STREAMS_APP.value,
            dry_run=False,
            local_chart_path=Path("my/fake/dir"),
        )

    @patch("kpops.pipeline_deployer.streams_bootstrap.helm_wrapper")
    def test_should_call_helm_upgrade_install_for_producer_app(self, wrapper):
        handler = AppHandler(helm_wrapper=wrapper)
        handler.install_app(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app_type=ApplicationType.PRODUCER_APP,
            dry_run=False,
        )
        wrapper.helm_upgrade_install.assert_called_once_with(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app=ApplicationType.PRODUCER_APP.value,
            dry_run=False,
            local_chart_path=None,
        )

    @patch("kpops.pipeline_deployer.streams_bootstrap.helm_wrapper")
    def test_should_call_helm_upgrade_install_for_producer_overriding_repo(
        self, wrapper
    ):
        handler = AppHandler(helm_wrapper=wrapper)
        handler.install_app(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app_type=ApplicationType.PRODUCER_APP,
            dry_run=False,
            local_chart_path=Path("my/fake/dir"),
        )
        wrapper.helm_upgrade_install.assert_called_once_with(
            release_name="test-release",
            namespace="test-namespace",
            values={"commandLine": "test"},
            app=ApplicationType.PRODUCER_APP.value,
            dry_run=False,
            local_chart_path=Path("my/fake/dir"),
        )

    @patch("kpops.pipeline_deployer.streams_bootstrap.helm_wrapper")
    def test_should_call_run_command_method_when_helm_uninstall(self, wrapper):
        handler = AppHandler(helm_wrapper=wrapper)
        handler.uninstall_app(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
            suffix="",
        )
        wrapper.helm_uninstall.assert_called_once_with(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
            suffix="",
        )
