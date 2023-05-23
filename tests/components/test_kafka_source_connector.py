from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig, TopicNameConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.component_handlers.kafka_connect.model import KafkaConnectConfig
from kpops.components.base_components.kafka_connector import KafkaSourceConnector
from kpops.components.base_components.models.from_section import (
    FromSection,
    FromTopic,
    InputTopicTypes,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.utils.environment import environ

DEFAULTS_PATH = Path(__file__).parent / "resources"
CONNECTOR_NAME = "test-connector-with-long-name-0123456789abcdefghijklmnop"
CONNECTOR_CLEAN_NAME = "test-connector-with-long-name-0123456789abcdef-clean"


class TestKafkaSourceConnector:
    @pytest.fixture
    def config(slef) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            topic_name_config=TopicNameConfig(
                default_error_topic_name="${component_type}-error-topic",
                default_output_topic_name="${component_type}-output-topic",
            ),
            broker="broker:9092",
            helm_diff_config=HelmDiffConfig(
                enable=False,
            ),
        )

    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    @pytest.fixture
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.kafka_connector.Helm"
        ).return_value

    def test_from_section_raises_exception(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        with pytest.raises(NotImplementedError):
            KafkaSourceConnector(
                name="test-connector",
                config=config,
                handlers=handlers,
                app=KafkaConnectConfig(),
                namespace="test-namespace",
                from_=FromSection(
                    topics={
                        "connector-topic": FromTopic(type=InputTopicTypes.INPUT),
                    }
                ),
            )

    def test_deploy_order(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        connector = KafkaSourceConnector(
            name="test-connector",
            config=config,
            handlers=handlers,
            app=KafkaConnectConfig(),
            namespace="test-namespace",
            to=ToSection(
                topics={
                    "${output_topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

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
            mocker.call.mock_create_connector(
                connector_name="test-connector",
                kafka_connect_config=connector.app,
                dry_run=True,
            ),
        ]

    def test_destroy(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        environ["KPOPS_KAFKA_CONNECT_RESETTER_OFFSET_TOPIC"] = "kafka-connect-offsets"
        connector = KafkaSourceConnector(
            name="test-connector",
            config=config,
            handlers=handlers,
            app=KafkaConnectConfig(),
            namespace="test-namespace",
            to=ToSection(
                topics={
                    "${output_topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )
        assert connector.handlers.connector_handler

        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )

        connector.destroy(dry_run=True)

        mock_destroy_connector.assert_called_once_with(
            connector_name="test-connector",
            dry_run=True,
        )

    def test_reset(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        mocker: MockerFixture,
    ):
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=KafkaConnectConfig(),
            namespace="test-namespace",
            offset_topic="kafka-connect-offsets",
            to=ToSection(
                topics={
                    "${output_topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

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

        connector.reset(dry_run=True)

        assert mock.mock_calls == [
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                namespace="test-namespace",
                release_name=CONNECTOR_CLEAN_NAME,
                dry_run=True,
            ),
            mocker.call.helm.upgrade_install(
                release_name=CONNECTOR_CLEAN_NAME,
                namespace="test-namespace",
                chart="bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run=True,
                flags=HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
                values={
                    "connectorType": "source",
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_NAME,
                        "offsetTopic": "kafka-connect-offsets",
                    },
                    "nameOverride": CONNECTOR_NAME,
                },
            ),
            mocker.call.helm.uninstall(
                namespace="test-namespace",
                release_name=CONNECTOR_CLEAN_NAME,
                dry_run=True,
            ),
        ]

        mock_delete_topics.assert_not_called()

    def test_clean(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        mocker: MockerFixture,
    ):
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=KafkaConnectConfig(),
            namespace="test-namespace",
            offset_topic="kafka-connect-offsets",
            to=ToSection(
                topics={
                    "${output_topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )
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

        connector.clean(dry_run=True)

        assert mock.mock_calls == [
            mocker.call.mock_delete_topics(connector.to, dry_run=True),
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                namespace="test-namespace",
                release_name=CONNECTOR_CLEAN_NAME,
                dry_run=True,
            ),
            mocker.call.helm.upgrade_install(
                release_name=CONNECTOR_CLEAN_NAME,
                namespace="test-namespace",
                chart="bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run=True,
                flags=HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
                values={
                    "connectorType": "source",
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_NAME,
                        "offsetTopic": "kafka-connect-offsets",
                    },
                    "nameOverride": CONNECTOR_NAME,
                },
            ),
            mocker.call.helm.uninstall(
                namespace="test-namespace",
                release_name=CONNECTOR_CLEAN_NAME,
                dry_run=True,
            ),
        ]

    def test_clean_without_to(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        mocker: MockerFixture,
    ):
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=KafkaConnectConfig(),
            namespace="test-namespace",
            offset_topic="kafka-connect-offsets",
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

        connector.clean(dry_run=True)

        assert mock.mock_calls == [
            mocker.call.helm.add_repo(
                "bakdata-kafka-connect-resetter",
                "https://bakdata.github.io/kafka-connect-resetter/",
                RepoAuthFlags(),
            ),
            mocker.call.helm.uninstall(
                namespace="test-namespace",
                release_name=CONNECTOR_CLEAN_NAME,
                dry_run=True,
            ),
            mocker.call.helm.upgrade_install(
                release_name=CONNECTOR_CLEAN_NAME,
                namespace="test-namespace",
                chart="bakdata-kafka-connect-resetter/kafka-connect-resetter",
                dry_run=True,
                flags=HelmUpgradeInstallFlags(
                    version="1.0.4",
                    wait=True,
                    wait_for_jobs=True,
                ),
                values={
                    "connectorType": "source",
                    "config": {
                        "brokers": "broker:9092",
                        "connector": CONNECTOR_NAME,
                        "offsetTopic": "kafka-connect-offsets",
                    },
                    "nameOverride": CONNECTOR_NAME,
                },
            ),
            mocker.call.helm.uninstall(
                namespace="test-namespace",
                release_name=CONNECTOR_CLEAN_NAME,
                dry_run=True,
            ),
        ]

        mock_delete_topics.assert_not_called()
