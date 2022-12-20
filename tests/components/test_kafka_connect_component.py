import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig, TopicNameConfig
from kpops.cli.pipeline_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.handler import KafkaConnectorType
from kpops.component_handlers.kafka_connect.model import KafkaConnectConfig
from kpops.components.base_components.kafka_connect import (
    KafkaSinkConnector,
    KafkaSourceConnector,
)
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

DEFAULTS_PATH = Path(__file__).parent / "resources"


@pytest.fixture
def config():
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
def handlers() -> ComponentHandlers:
    return ComponentHandlers(
        schema_handler=MagicMock(),
        app_handler=MagicMock(),
        connector_handler=MagicMock(),
        topic_handler=MagicMock(),
    )


class TestKafkaConnectorSink:
    def test_connector_config_parsing(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        topic_name = "connector-topic"
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(**{"topics": topic_name}),
        )
        assert getattr(connector.app, "topics") == topic_name

        topic_pattern = ".*"
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(**{"topics.regex": topic_pattern}),
        )
        assert getattr(connector.app, "topics.regex") == topic_pattern

        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${error_topic_name}": TopicConfig(type=OutputTopicTypes.ERROR),
                }
            ),
        )
        assert (
            getattr(connector.app, "errors.deadletterqueue.topic.name")
            == "kafka-sink-connector-error-topic"
        )

    def test_from_section_parsing_input_topic(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        topic1 = "connector-topic1"
        topic2 = "connector-topic2"
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            from_=FromSection(
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
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        topic_pattern = ".*"
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            from_=FromSection(
                topics={topic_pattern: FromTopic(type=InputTopicTypes.INPUT_PATTERN)}
            ),
        )
        assert getattr(connector.app, "topics.regex") == topic_pattern

    def test_deploy_order(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${topic_name}": TopicConfig(
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
        mock.assert_has_calls(
            [
                mocker.call.mock_create_topics(to_section=connector.to, dry_run=True),
                mocker.call.mock_create_connector(
                    connector_name="test-connector",
                    kafka_connect_config=connector.app,
                    dry_run=True,
                ),
            ],
        )

    def test_clean(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )
        mock_clean_connector = mocker.patch.object(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_destroy_connector, "mock_destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        connector.destroy(dry_run=True, clean=True, delete_outputs=True)
        mock.assert_has_calls(
            [
                mocker.call.mock_destroy_connector(
                    connector_name="test-connector",
                    dry_run=True,
                ),
                mocker.call.mock_delete_topics(connector.to, dry_run=True),
                mocker.call.mock_clean_connector(
                    connector_name="test-connector",
                    connector_type=KafkaConnectorType.SINK,
                    dry_run=True,
                    retain_clean_jobs=True,
                    delete_consumer_group=True,
                ),
            ]
        )

    def test_reset(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )
        mock_clean_connector = mocker.patch.object(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_destroy_connector, "mock_destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        connector.destroy(dry_run=True, clean=True, delete_outputs=False)
        mock.assert_has_calls(
            [
                mocker.call.mock_destroy_connector(
                    connector_name="test-connector",
                    dry_run=True,
                ),
                mocker.call.mock_clean_connector(
                    connector_name="test-connector",
                    connector_type=KafkaConnectorType.SINK,
                    dry_run=True,
                    retain_clean_jobs=True,
                    delete_consumer_group=False,
                ),
            ]
        )
        mock_delete_topics.assert_not_called()

    def test_clean_without_to(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        connector = KafkaSinkConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
        )

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )
        mock_clean_connector = mocker.patch.object(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_destroy_connector, "mock_destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        connector.destroy(dry_run=True, clean=True, delete_outputs=True)
        mock.assert_has_calls(
            [
                mocker.call.mock_destroy_connector(
                    connector_name="test-connector",
                    dry_run=True,
                ),
                mocker.call.mock_clean_connector(
                    connector_name="test-connector",
                    connector_type=KafkaConnectorType.SINK,
                    dry_run=True,
                    retain_clean_jobs=True,
                    delete_consumer_group=True,
                ),
            ]
        )
        mock_delete_topics.assert_not_called()


class TestKafkaConnectorSource:
    def test_from_section_raises_exception(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        with pytest.raises(NotImplementedError):
            KafkaSourceConnector(
                name="test-connector",
                handlers=handlers,
                config=config,
                app=KafkaConnectConfig(),
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
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${topic_name}": TopicConfig(
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
        mock.assert_has_calls(
            [
                mocker.call.mock_create_topics(to_section=connector.to, dry_run=True),
                mocker.call.mock_create_connector(
                    connector_name="test-connector",
                    kafka_connect_config=connector.app,
                    dry_run=True,
                ),
            ],
        )

    def test_clean(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        os.environ[
            "KPOPS_KAFKA_CONNECT_RESETTER_OFFSET_TOPIC"
        ] = "kafka-connect-offsets"
        connector = KafkaSourceConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )
        assert connector.handlers.connector_handler

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )
        mock_clean_connector = mocker.spy(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_destroy_connector, "mock_destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        connector.destroy(dry_run=True, clean=True, delete_outputs=True)
        mock.assert_has_calls(
            [
                mocker.call.mock_destroy_connector(
                    connector_name="test-connector",
                    dry_run=True,
                ),
                mocker.call.mock_delete_topics(connector.to, dry_run=True),
                mocker.call.mock_clean_connector(
                    connector_name="test-connector",
                    connector_type=KafkaConnectorType.SOURCE,
                    dry_run=True,
                    retain_clean_jobs=True,
                    offset_topic="kafka-connect-offsets",
                ),
            ]
        )

    def test_clean_without_to(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        os.environ[
            "KPOPS_KAFKA_CONNECT_RESETTER_OFFSET_TOPIC"
        ] = "kafka-connect-offsets"
        connector = KafkaSourceConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
        )
        assert connector.to is None

        assert connector.handlers.connector_handler

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )
        mock_clean_connector = mocker.spy(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_destroy_connector, "mock_destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        connector.destroy(dry_run=True, clean=True, delete_outputs=True)
        mock.assert_has_calls(
            [
                mocker.call.mock_destroy_connector(
                    connector_name="test-connector",
                    dry_run=True,
                ),
                mocker.call.mock_clean_connector(
                    connector_name="test-connector",
                    connector_type=KafkaConnectorType.SOURCE,
                    dry_run=True,
                    retain_clean_jobs=True,
                    offset_topic="kafka-connect-offsets",
                ),
            ]
        )

        mock_delete_topics.assert_not_called()

    def test_reset(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        os.environ[
            "KPOPS_KAFKA_CONNECT_RESETTER_OFFSET_TOPIC"
        ] = "kafka-connect-offsets"
        connector = KafkaSourceConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

        assert connector.handlers.connector_handler

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )
        mock_clean_connector = mocker.spy(
            connector.handlers.connector_handler, "clean_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_destroy_connector, "mock_destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        connector.destroy(dry_run=True, clean=True, delete_outputs=False)
        mock.assert_has_calls(
            [
                mocker.call.mock_destroy_connector(
                    connector_name="test-connector",
                    dry_run=True,
                ),
                mocker.call.mock_clean_connector(
                    connector_name="test-connector",
                    connector_type=KafkaConnectorType.SOURCE,
                    dry_run=True,
                    retain_clean_jobs=True,
                    offset_topic="kafka-connect-offsets",
                ),
            ]
        )
        mock_delete_topics.assert_not_called()

    def test_destroy(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        connector = KafkaSourceConnector(
            name="test-connector",
            handlers=handlers,
            config=config,
            app=KafkaConnectConfig(),
            to=ToSection(
                topics={
                    "${topic_name}": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

        assert connector.handlers.connector_handler

        mock_delete_topics = mocker.patch.object(
            connector.handlers.topic_handler, "delete_topics"
        )
        mock_destroy_connector = mocker.patch.object(
            connector.handlers.connector_handler, "destroy_connector"
        )
        mock_clean_connector = mocker.spy(
            connector.handlers.connector_handler, "clean_connector"
        )
        mock_helm_upgrade_install = mocker.patch.object(
            connector.handlers.connector_handler._helm_wrapper,
            "helm_upgrade_install",
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_delete_topics, "mock_delete_topics")
        mock.attach_mock(mock_destroy_connector, "mock_destroy_connector")
        mock.attach_mock(mock_clean_connector, "mock_clean_connector")
        connector.destroy(dry_run=True, clean=False, delete_outputs=False)
        mock.assert_has_calls(
            [
                mocker.call.mock_destroy_connector(
                    connector_name="test-connector",
                    dry_run=True,
                ),
            ]
        )
        mock_delete_topics.assert_not_called()
        mock_helm_upgrade_install.assert_not_called()
