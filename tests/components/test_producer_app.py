from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig, TopicNameConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.components import ProducerApp
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestProducerApp:
    PRODUCER_APP_NAME = "test-producer-app-with-long-name-0123456789abcdefghijklmnop"
    PRODUCER_APP_CLEAN_NAME = "test-producer-app-with-long-name-0123456789abc-clean"

    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    @pytest.fixture
    def config(self) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            topic_name_config=TopicNameConfig(
                default_error_topic_name="${component_type}-error-topic",
                default_output_topic_name="${component_type}-output-topic",
            ),
            pipeline_prefix="",
        )

    @pytest.fixture
    def producer_app(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ) -> ProducerApp:
        return ProducerApp(
            name=self.PRODUCER_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "version": "2.4.2",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "clean_schemas": True,
                "to": {
                    "topics": {
                        "${output_topic_name}": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )

    def test_output_topics(self, config: PipelineConfig, handlers: ComponentHandlers):
        producer_app = ProducerApp(
            name=self.PRODUCER_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${output_topic_name}": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            type=OutputTopicTypes.EXTRA,
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )

        assert producer_app.app.streams.output_topic == "producer-output-topic"
        assert producer_app.app.streams.extra_output_topics == {
            "first-extra-topic": "extra-topic-1"
        }

    def test_deploy_order(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_create_topics = mocker.patch.object(
            producer_app.handlers.topic_handler, "create_topics"
        )

        mock_helm_upgrade_install = mocker.patch.object(
            producer_app.helm, "upgrade_install"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_create_topics, "mock_create_topics")
        mock.attach_mock(mock_helm_upgrade_install, "mock_helm_upgrade_install")

        producer_app.deploy(dry_run=True)
        mock.assert_has_calls(
            [
                mocker.call.mock_create_topics(
                    to_section=producer_app.to, dry_run=True
                ),
                mocker.call.mock_helm_upgrade_install(
                    self.PRODUCER_APP_NAME,
                    "bakdata-streams-bootstrap/producer-app",
                    True,
                    "test-namespace",
                    {
                        "namespace": "test-namespace",
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "producer-output-topic",
                        },
                    },
                    HelmUpgradeInstallFlags(
                        force=False,
                        repo_auth_flags=RepoAuthFlags(
                            username=None,
                            password=None,
                            ca_file=None,
                            insecure_skip_tls_verify=False,
                        ),
                        timeout="5m0s",
                        version="2.4.2",
                        wait=True,
                        wait_for_jobs=False,
                    ),
                ),
            ],
        )

    def test_destroy(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_helm_uninstall = mocker.patch.object(producer_app.helm, "uninstall")

        producer_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", self.PRODUCER_APP_NAME, True
        )

    def should_not_reset_producer_app(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            producer_app.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(producer_app.helm, "uninstall")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        producer_app.clean(dry_run=True)

        mock.assert_has_calls(
            [
                mocker.call.helm_uninstall(
                    "test-namespace", self.PRODUCER_APP_CLEAN_NAME, True
                ),
                mocker.call.helm_upgrade_install(
                    self.PRODUCER_APP_CLEAN_NAME,
                    "bakdata-streams-bootstrap/producer-app-cleanup-job",
                    True,
                    "test-namespace",
                    {
                        "namespace": "test-namespace",
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "producer-output-topic",
                            "deleteOutput": True,
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.4.2", wait=True, wait_for_jobs=True
                    ),
                ),
                mocker.call.helm_uninstall(
                    "test-namespace", self.PRODUCER_APP_CLEAN_NAME, True
                ),
            ]
        )

    def test_should_clean_producer_app_and_deploy_clean_up_job_and_delete_clean_up(
        self, mocker: MockerFixture, producer_app: ProducerApp
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            producer_app.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(producer_app.helm, "uninstall")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        producer_app.clean(dry_run=True)

        mock.assert_has_calls(
            [
                mocker.call.helm_uninstall(
                    "test-namespace", self.PRODUCER_APP_CLEAN_NAME, True
                ),
                mocker.call.helm_upgrade_install(
                    self.PRODUCER_APP_CLEAN_NAME,
                    "bakdata-streams-bootstrap/producer-app-cleanup-job",
                    True,
                    "test-namespace",
                    {
                        "namespace": "test-namespace",
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "producer-output-topic",
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.4.2", wait=True, wait_for_jobs=True
                    ),
                ),
                mocker.call.helm_uninstall(
                    "test-namespace", self.PRODUCER_APP_CLEAN_NAME, True
                ),
            ]
        )
