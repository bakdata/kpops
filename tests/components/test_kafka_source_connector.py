from unittest.mock import ANY, MagicMock

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
from kpops.components.base_components.kafka_connector import KafkaSourceConnector
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
from kpops.utils.environment import ENV
from tests.components.test_kafka_connector import (
    CONNECTOR_CLEAN_FULL_NAME,
    CONNECTOR_CLEAN_RELEASE_NAME,
    CONNECTOR_FULL_NAME,
    CONNECTOR_NAME,
    RESETTER_NAMESPACE,
    TestKafkaConnector,
)

CONNECTOR_TYPE = KafkaConnectorType.SOURCE.value
CLEAN_SUFFIX = "-clean"
OFFSETS_TOPIC = "kafka-connect-offsets"


class TestKafkaSourceConnector(TestKafkaConnector):
    @pytest.fixture()
    def connector(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ) -> KafkaSourceConnector:
        return KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
            to=ToSection(
                topics={
                    TopicName("${output_topic_name}"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
            offset_topic=OFFSETS_TOPIC,
        )

    def test_from_section_raises_exception(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ):
        with pytest.raises(NotImplementedError):
            KafkaSourceConnector(
                name=CONNECTOR_NAME,
                config=config,
                handlers=handlers,
                app=connector_config,
                resetter_namespace=RESETTER_NAMESPACE,
                from_=FromSection(  # pyright: ignore[reportGeneralTypeIssues] wrong diagnostic when using TopicName as topics key type
                    topics={
                        TopicName("connector-topic"): FromTopic(
                            type=InputTopicTypes.INPUT
                        ),
                    }
                ),
            )

    def test_deploy_order(
        self,
        connector: KafkaSourceConnector,
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
        connector: KafkaSourceConnector,
        mocker: MockerFixture,
    ):
        ENV["KPOPS_KAFKA_CONNECT_RESETTER_OFFSET_TOPIC"] = OFFSETS_TOPIC
        assert connector.handlers.connector_handler

        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )

        connector.destroy(dry_run=True)

        mock_destroy_connector.assert_called_once_with(
            CONNECTOR_FULL_NAME, dry_run=True
        )

    def test_reset_when_dry_run_is_true(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
    ):
        assert connector.handlers.connector_handler

        connector.reset(dry_run=True)

        dry_run_handler_mock.print_helm_diff.assert_called_once()

    def test_reset_when_dry_run_is_false(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
        helm_mock: MagicMock,
        mocker: MockerFixture,
    ):
        assert connector.handlers.connector_handler
        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_clean_connector = mocker.spy(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        connector.reset(dry_run=False)

        assert mock.mock_calls == [
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                False,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm.upgrade_install(
                CONNECTOR_CLEAN_RELEASE_NAME,
                "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                False,
                RESETTER_NAMESPACE,
                {
                    "connectorType": CONNECTOR_TYPE,
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_FULL_NAME,
                        "offsetTopic": OFFSETS_TOPIC,
                    },
                    "nameOverride": CONNECTOR_CLEAN_FULL_NAME,
                },
                HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                False,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]
        mock_delete_topics.assert_not_called()
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    def test_clean_when_dry_run_is_true(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
    ):
        assert connector.handlers.connector_handler

        connector.clean(dry_run=True)

        dry_run_handler_mock.print_helm_diff.assert_called_once()

    def test_clean_when_dry_run_is_false(
        self,
        connector: KafkaSourceConnector,
        helm_mock: MagicMock,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ):
        assert connector.handlers.connector_handler

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_clean_connector = mocker.spy(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        mock.attach_mock(helm_mock, "helm")

        dry_run = False
        connector.clean(dry_run)

        assert mock.mock_calls == [
            mocker.call.mock_delete_topics(connector.to, dry_run=dry_run),
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm.upgrade_install(
                CONNECTOR_CLEAN_RELEASE_NAME,
                "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run,
                RESETTER_NAMESPACE,
                {
                    "nameOverride": CONNECTOR_CLEAN_FULL_NAME,
                    "connectorType": CONNECTOR_TYPE,
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_FULL_NAME,
                        "offsetTopic": OFFSETS_TOPIC,
                    },
                },
                HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

        dry_run_handler_mock.print_helm_diff.assert_not_called()

    def test_clean_without_to_when_dry_run_is_false(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
            offset_topic=OFFSETS_TOPIC,
        )
        assert connector.to is None

        assert connector.handlers.connector_handler

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_clean_connector = mocker.spy(
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
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm.upgrade_install(
                CONNECTOR_CLEAN_RELEASE_NAME,
                "bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run,
                RESETTER_NAMESPACE,
                {
                    "nameOverride": CONNECTOR_CLEAN_FULL_NAME,
                    "connectorType": CONNECTOR_TYPE,
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_FULL_NAME,
                        "offsetTopic": OFFSETS_TOPIC,
                    },
                },
                HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
            ),
            mocker.call.helm.uninstall(
                RESETTER_NAMESPACE,
                CONNECTOR_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

        mock_delete_topics.assert_not_called()
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    def test_clean_without_to_when_dry_run_is_true(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        dry_run_handler_mock: MagicMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
            offset_topic=OFFSETS_TOPIC,
        )
        assert connector.to is None

        assert connector.handlers.connector_handler

        connector.clean(dry_run=True)

        dry_run_handler_mock.print_helm_diff.assert_called_once()
