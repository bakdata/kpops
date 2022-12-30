# TODO: Migrate tests for the new implementation
# from pathlib import Path
# from unittest.mock import MagicMock
#
# import pytest
# from pytest_mock import MockerFixture
#
# from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
# from kpops.component_handlers.helm_wrapper.model import (
#     HelmConfig,
#     HelmDiffConfig,
#     HelmRepoConfig,
#     HelmUpgradeInstallFlags,
#     RepoAuthFlags,
# )
# from kpops.component_handlers.streams_bootstrap.app_handler import KafkaAppHandler
#
# DEFAULTS_PATH = Path(__file__).parent / "resources"
#
#
# class TestKafkaAppDeployment:
#     @pytest.fixture(autouse=True)
#     def helm_wrapper_mock(self, mocker: MockerFixture) -> MagicMock:
#         return mocker.patch(
#             "kpops.component_handlers.kubernetes_app.kubernetes_app_handler.Helm"
#         ).return_value
#
#     @pytest.fixture(autouse=True)
#     def kafka_app_handler(self, helm_wrapper_mock: MagicMock) -> KafkaAppHandler:
#         helm_repo_config = HelmRepoConfig(
#             repository_name="bakdata-streams-bootstrap",
#             url="https://bakdata.github.io/streams-bootstrap/",
#             version="2.4.2",
#         )
#
#         return KafkaAppHandler(
#             HelmConfig(), helm_repo_config, HelmDiff(HelmDiffConfig())
#         )
#
#     def test_should_call_helm_repo_add_when_initializing_app_handler(
#         self, helm_wrapper_mock, kafka_app_handler: KafkaAppHandler
#     ):
#         helm_wrapper_mock.add_repo.assert_called_once_with(
#             "bakdata-streams-bootstrap",
#             "https://bakdata.github.io/streams-bootstrap/",
#             RepoAuthFlags(),
#         )
#
#     def test_should_call_helm_upgrade_install_for_streams_app(
#         self, helm_wrapper_mock: MagicMock, kafka_app_handler
#     ):
#         kafka_app_handler.install_app(
#             "test-release",
#             f"{kafka_app_handler.repository_name}/{ApplicationType.STREAMS_APP.value}",
#             "test-namespace",
#             {"commandLine": "test"},
#             False,
#         )
#         helm_wrapper_mock.upgrade_install.assert_called_once_with(
#             release_name="test-release",
#             namespace="test-namespace",
#             chart=f"{kafka_app_handler.repository_name}/{ApplicationType.STREAMS_APP.value}",
#             values={"commandLine": "test"},
#             dry_run=False,
#             flags=HelmUpgradeInstallFlags(version="2.4.2"),
#         )
#
#     def test_should_call_helm_upgrade_install_for_producer_app(
#         self, helm_wrapper_mock: MagicMock, kafka_app_handler
#     ):
#         kafka_app_handler.install_app(
#             release_name="test-release",
#             chart=f"{kafka_app_handler.repository_name}/{ApplicationType.PRODUCER_APP.value}",
#             namespace="test-namespace",
#             values={"commandLine": "test"},
#             dry_run=False,
#         )
#         helm_wrapper_mock.upgrade_install.assert_called_once_with(
#             release_name="test-release",
#             chart=f"{kafka_app_handler.repository_name}/{ApplicationType.PRODUCER_APP.value}",
#             dry_run=False,
#             namespace="test-namespace",
#             values={"commandLine": "test"},
#             flags=HelmUpgradeInstallFlags(version="2.4.2"),
#         )
#
#     def test_should_call_run_command_method_when_helm_uninstall(
#         self, helm_wrapper_mock: MagicMock, kafka_app_handler
#     ):
#         kafka_app_handler.uninstall_app(
#             namespace="test-namespace",
#             release_name="test-release",
#             dry_run=False,
#         )
#         helm_wrapper_mock.uninstall.assert_called_once_with(
#             namespace="test-namespace",
#             release_name="test-release",
#             dry_run=False,
#         )
