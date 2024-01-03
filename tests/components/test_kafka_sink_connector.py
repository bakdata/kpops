from unittest.mock import ANY, MagicMock, call

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectorConfig,
    KafkaConnectorType,
)
from kpops.components import KafkaSinkConnector
from kpops.components.base_components.kafka_connector import KafkaConnectorResetter
from kpops.components.base_components.models.from_section import (
    FromSection,
    FromTopic,
    InputTopicTypes,
    TopicName,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.config import KpopsConfig
from kpops.utils.colorify import magentaify
from tests.components.test_kafka_connector import (
    CONNECTOR_CLEAN_FULL_NAME,
    CONNECTOR_CLEAN_RELEASE_NAME,
    CONNECTOR_FULL_NAME,
    CONNECTOR_NAME,
    TestKafkaConnector,
)


class TestKafkaSinkConnector(TestKafkaConnector):
    @pytest.fixture()
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.components.base_components.kafka_connector.log.info")

    @pytest.fixture()
    def connector(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ) -> KafkaSinkConnector:
        return KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace="test-namespace",
            to=ToSection(
                topics={
                    TopicName("${output_topic_name}"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

    def test_connector_config_parsing(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ):
        topic_name = "connector-topic"
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=KafkaConnectorConfig(
                **{**connector_config.model_dump(), "topics": topic_name}
            ),
            resetter_namespace="test-namespace",
        )
        assert getattr(connector.app, "topics") == topic_name

        topic_pattern = ".*"
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=KafkaConnectorConfig(
                **{**connector_config.model_dump(), "topics.regex": topic_pattern}
            ),
            resetter_namespace="test-namespace",
        )
        assert getattr(connector.app, "topics.regex") == topic_pattern

    def test_from_section_parsing_input_topic(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ):
        topic1 = TopicName("connector-topic1")
        topic2 = TopicName("connector-topic2")
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace="test-namespace",
            from_=FromSection(  # pyright: ignore[reportGeneralTypeIssues] wrong diagnostic when using TopicName as topics key type
                topics={
                    topic1: FromTopic(type=InputTopicTypes.INPUT),
                    topic2: FromTopic(type=InputTopicTypes.INPUT),
                }
            ),
        )
        assert getattr(connector.app, "topics") == f"{topic1},{topic2}"

        topic3 = "connector-topic3"
        connector.add_input_topics([topic1, topic3])
        assert getattr(connector.app, "topics") == f"{topic1},{topic2},{topic3}"

    def test_from_section_parsing_input_pattern(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ):
        topic_pattern = TopicName(".*")
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace="test-namespace",
            from_=FromSection(  # pyright: ignore[reportGeneralTypeIssues] wrong diagnostic when using TopicName as topics key type
                topics={topic_pattern: FromTopic(type=InputTopicTypes.PATTERN)}
            ),
        )
        assert getattr(connector.app, "topics.regex") == topic_pattern

    def test_deploy_order(
        self,
        connector: KafkaSinkConnector,
        mocker: MockerFixture,
    ):
        mock_create_topics = mocker.patch.object(
            connector.handlers.topic_handler, "create_topics"
        )
        mock_create_connector = mocker.patch.object(
            connector.handlers.connector_handler, "create_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_create_topics, "mock_create_topics")
        mock.attach_mock(mock_create_connector, "mock_create_connector")
        connector.deploy(dry_run=True)
        assert mock.mock_calls == [
            mocker.call.mock_create_topics(to_section=connector.to, dry_run=True),
            mocker.call.mock_create_connector(connector.app, dry_run=True),
        ]

    def test_destroy(
        self,
        connector: KafkaSinkConnector,
        mocker: MockerFixture,
    ):
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )

        connector.destroy(dry_run=True)

        mock_destroy_connector.assert_called_once_with(
            CONNECTOR_FULL_NAME, dry_run=True
        )

    def test_reset_when_dry_run_is_true(
        self,
        connector: KafkaSinkConnector,
        dry_run_handler_mock: MagicMock,
    ):
        dry_run = True
        connector.reset(dry_run=dry_run)

        dry_run_handler_mock.print_helm_diff.assert_called_once()

    def test_reset_when_dry_run_is_false(
        self,
        connector: KafkaSinkConnector,
        dry_run_handler_mock: MagicMock,
        helm_mock: MagicMock,
        mocker: MockerFixture,
    ):
        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_clean_connector = mocker.patch.object(
            connector.handlers.connector_handler, "clean_connector"
        )
        resetter = connector._resetter
        assert isinstance(resetter, KafkaConnectorResetter)

        mock_resetter_reset = mocker.spy(resetter, "reset")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        dry_run = False
        connector.reset(dry_run=dry_run)
        mock_resetter_reset.assert_called_once_with(dry_run)

        mock.assert_has_calls(
            [
                mocker.call.helm.add_repo(
                    "bakdata-kafka-connect-resetter",
                    "https://bakdata.github.io/kafka-connect-resetter/",
                    RepoAuthFlags(),
                ),
                mocker.call.helm.uninstall(
                    "test-namespace",
                    CONNECTOR_CLEAN_RELEASE_NAME,
                    dry_run,
                ),
                ANY,  # __bool__
                ANY,  # __str__
                mocker.call.helm.upgrade_install(
                    CONNECTOR_CLEAN_RELEASE_NAME,
                    "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                    dry_run,
                    "test-namespace",
                    {
                        "nameOverride": CONNECTOR_CLEAN_FULL_NAME,
                        "connectorType": "sink",
                        "config": {
                            "brokers": "broker:9092",
                            "connector": CONNECTOR_FULL_NAME,
                            "deleteConsumerGroup": False,
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="1.0.4",
                        wait=True,
                        wait_for_jobs=True,
                    ),
                ),
                mocker.call.helm.uninstall(
                    "test-namespace",
                    CONNECTOR_CLEAN_RELEASE_NAME,
                    dry_run,
                ),
                ANY,  # __bool__
                ANY,  # __str__
            ]
        )

        dry_run_handler_mock.print_helm_diff.assert_not_called()
        mock_delete_topics.assert_not_called()

    def test_clean_when_dry_run_is_true(
        self,
        connector: KafkaSinkConnector,
        dry_run_handler_mock: MagicMock,
    ):
        dry_run = True
        connector.clean(dry_run=dry_run)
        dry_run_handler_mock.print_helm_diff.assert_called_once()

    def test_clean_when_dry_run_is_false(
        self,
        connector: KafkaSinkConnector,
        helm_mock: MagicMock,
        log_info_mock: MagicMock,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ):
        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_clean_connector = mocker.patch.object(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        dry_run = False
        connector.clean(dry_run=dry_run)

        assert log_info_mock.mock_calls == [
            call.log_info(
                magentaify(
                    f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {CONNECTOR_FULL_NAME}"
                )
            ),
            call.log_info(
                magentaify(
                    f"Connector Cleanup: deploy Connect {KafkaConnectorType.SINK.value} resetter for {CONNECTOR_FULL_NAME}"
                )
            ),
            call.log_info(magentaify("Connector Cleanup: uninstall Kafka Resetter.")),
        ]

        assert mock.mock_calls == [
            mocker.call.mock_delete_topics(connector.to, dry_run=dry_run),
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                "test-namespace",
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm.upgrade_install(
                CONNECTOR_CLEAN_RELEASE_NAME,
                "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run,
                "test-namespace",
                {
                    "nameOverride": CONNECTOR_CLEAN_FULL_NAME,
                    "connectorType": "sink",
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_FULL_NAME,
                        "deleteConsumerGroup": True,
                    },
                },
                HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
            ),
            mocker.call.helm.uninstall(
                "test-namespace",
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    def test_clean_without_to_when_dry_run_is_true(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        dry_run_handler_mock: MagicMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace="test-namespace",
        )

        dry_run = True
        connector.clean(dry_run)
        dry_run_handler_mock.print_helm_diff.assert_called_once()

    def test_clean_without_to_when_dry_run_is_false(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaSinkConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace="test-namespace",
        )

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_clean_connector = mocker.patch.object(
            connector.handlers.connector_handler, "clean_connector"
        )
        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        dry_run = False
        connector.clean(dry_run)

        assert mock.mock_calls == [
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(
                    username=None,
                    password=None,
                    ca_file=None,
                    insecure_skip_tls_verify=False,
                ),
            ),
            mocker.call.helm.uninstall(
                "test-namespace",
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm.upgrade_install(
                CONNECTOR_CLEAN_RELEASE_NAME,
                "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run,
                "test-namespace",
                {
                    "nameOverride": CONNECTOR_CLEAN_FULL_NAME,
                    "connectorType": "sink",
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_FULL_NAME,
                        "deleteConsumerGroup": True,
                    },
                },
                HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
            ),
            mocker.call.helm.uninstall(
                "test-namespace",
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

        dry_run_handler_mock.print_helm_diff.assert_not_called()
        mock_delete_topics.assert_not_called()
