import logging
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import HelmUpgradeInstallFlags
from kpops.components import ProducerApp
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
)
from kpops.config import KpopsConfig, TopicNameConfig

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestProducerApp:
    PRODUCER_APP_NAME = "test-producer-app-with-long-name-0123456789abcdefghijklmnop"
    PRODUCER_APP_CLEAN_NAME = "test-producer-app-with-long-n-clean"

    @pytest.fixture()
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    @pytest.fixture()
    def config(self) -> KpopsConfig:
        return KpopsConfig(
            defaults_path=DEFAULTS_PATH,
            topic_name_config=TopicNameConfig(
                default_error_topic_name="${component_type}-error-topic",
                default_output_topic_name="${component_type}-output-topic",
            ),
        )

    @pytest.fixture()
    def producer_app(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ) -> ProducerApp:
        return ProducerApp(
            name=self.PRODUCER_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "version": "2.4.2",
                "namespace": "test-namespace",
                "app": {
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

    def test_output_topics(self, config: KpopsConfig, handlers: ComponentHandlers):
        producer_app = ProducerApp(
            name=self.PRODUCER_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
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
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )

        assert producer_app.app.streams.output_topic == "${output_topic_name}"
        assert producer_app.app.streams.extra_output_topics == {
            "first-extra-topic": "extra-topic-1"
        }

    def test_deploy_order_when_dry_run_is_false(
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

        producer_app.deploy(dry_run=False)
        assert mock.mock_calls == [
            mocker.call.mock_create_topics(to_section=producer_app.to, dry_run=False),
            mocker.call.mock_helm_upgrade_install(
                "${pipeline_name}-" + self.PRODUCER_APP_NAME,
                "bakdata-streams-bootstrap/producer-app",
                False,
                "test-namespace",
                {
                    "nameOverride": "${pipeline_name}-" + self.PRODUCER_APP_NAME,
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "${output_topic_name}",
                    },
                },
                HelmUpgradeInstallFlags(
                    force=False,
                    username=None,
                    password=None,
                    ca_file=None,
                    insecure_skip_tls_verify=False,
                    timeout="5m0s",
                    version="2.4.2",
                    wait=True,
                    wait_for_jobs=False,
                ),
            ),
        ]

    def test_destroy(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_helm_uninstall = mocker.patch.object(producer_app.helm, "uninstall")

        producer_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", "${pipeline_name}-" + self.PRODUCER_APP_NAME, True
        )

    def test_should_not_reset_producer_app(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            producer_app.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(producer_app.helm, "uninstall")
        mock_helm_print_helm_diff = mocker.patch.object(
            producer_app.dry_run_handler, "print_helm_diff"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")
        mock.attach_mock(mock_helm_print_helm_diff, "print_helm_diff")

        producer_app.clean(dry_run=True)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace",
                "${pipeline_name}-" + self.PRODUCER_APP_CLEAN_NAME,
                True,
            ),
            mocker.call.helm_upgrade_install(
                "${pipeline_name}-" + self.PRODUCER_APP_CLEAN_NAME,
                "bakdata-streams-bootstrap/producer-app-cleanup-job",
                True,
                "test-namespace",
                {
                    "nameOverride": "${pipeline_name}-" + self.PRODUCER_APP_NAME,
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "${output_topic_name}",
                    },
                },
                HelmUpgradeInstallFlags(version="2.4.2", wait=True, wait_for_jobs=True),
            ),
            mocker.call.print_helm_diff(
                ANY,
                "${pipeline_name}-" + self.PRODUCER_APP_CLEAN_NAME,
                logging.getLogger("KafkaApp"),
            ),
            mocker.call.helm_uninstall(
                "test-namespace",
                "${pipeline_name}-" + self.PRODUCER_APP_CLEAN_NAME,
                True,
            ),
        ]

    def test_should_clean_producer_app_and_deploy_clean_up_job_and_delete_clean_up_with_dry_run_false(
        self, mocker: MockerFixture, producer_app: ProducerApp
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            producer_app.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(producer_app.helm, "uninstall")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        producer_app.clean(dry_run=False)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace",
                "${pipeline_name}-" + self.PRODUCER_APP_CLEAN_NAME,
                False,
            ),
            mocker.call.helm_upgrade_install(
                "${pipeline_name}-" + self.PRODUCER_APP_CLEAN_NAME,
                "bakdata-streams-bootstrap/producer-app-cleanup-job",
                False,
                "test-namespace",
                {
                    "nameOverride": "${pipeline_name}-" + self.PRODUCER_APP_NAME,
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "${output_topic_name}",
                    },
                },
                HelmUpgradeInstallFlags(version="2.4.2", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                "test-namespace",
                "${pipeline_name}-" + self.PRODUCER_APP_CLEAN_NAME,
                False,
            ),
        ]
