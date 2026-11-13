from typing import override
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from kpops.component_handlers import get_handlers
from kpops.component_handlers.kafka_connect.model import (
    ConnectorNewState,
    KafkaConnectorConfig,
    KafkaConnectorType,
    KafkaSourceConnectorConfig,
)
from kpops.components.base_components import ConsumesTopics
from kpops.components.base_components.kafka_connector import (
    KafkaSourceConnector,
)
from kpops.components.base_components.models import TopicName
from kpops.components.base_components.models.from_section import (
    FromSection,
    FromTopic,
    InputTopicTypes,
)
from kpops.components.base_components.models.to_section import (
    ToSection,
)
from kpops.components.common.topic import OutputTopicTypes, TopicConfig
from tests.components.test_kafka_connector import (
    CONNECTOR_FULL_NAME,
    CONNECTOR_NAME,
    TestKafkaConnector,
)

CONNECTOR_TYPE = KafkaConnectorType.SOURCE.value
CLEAN_SUFFIX = "-clean"
OFFSETS_TOPIC = "kafka-connect-offsets"


class TestKafkaSourceConnector(TestKafkaConnector):
    @override
    @pytest.fixture()
    def connector(
        self,
        connector_config: KafkaConnectorConfig,
    ) -> KafkaSourceConnector:
        return KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            to=ToSection(
                topics={
                    TopicName("${output_topic_name}"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                }
            ),
        )

    def test_supports_from_section(self) -> None:
        assert not issubclass(KafkaSourceConnector, ConsumesTopics)

    def test_connector_config_parsing(
        self, connector_config: KafkaConnectorConfig
    ) -> None:
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config={**connector_config.model_dump(), "topics": "a,b"},
        )
        assert isinstance(connector.config, KafkaSourceConnectorConfig)
        assert "topics" not in KafkaSourceConnectorConfig.model_fields
        assert connector.config.model_dump()["topics"] == "a,b"

    def test_source_connector_config_fields(
        self, connector_config: KafkaConnectorConfig
    ) -> None:
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config={
                **connector_config.model_dump(),
                "topic.creation.default.replication.factor": -1,
                "topic.creation.default.partitions": 3,
                "exactly.once.support": "required",
            },
        )
        assert connector.config.topic_creation_default_partitions == 3
        assert connector.config.exactly_once_support == "required"
        assert (
            connector.config.model_dump()
            | {
                "topic.creation.default.replication.factor": "-1",
                "topic.creation.default.partitions": "3",
                "exactly.once.support": "required",
            }
            == connector.config.model_dump()
        )

        with pytest.raises(ValidationError):
            KafkaSourceConnector(
                name=CONNECTOR_NAME,
                config={
                    **connector_config.model_dump(),
                    "transaction.boundary": "invalid",
                },
            )

    def test_substitute_in_typed_config_fields(
        self, connector_config: KafkaConnectorConfig
    ) -> None:
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config={
                **connector_config.model_dump(),
                "tasks.max": "${component.max_tasks}",
                "errors.log.enable": "${config.retain_clean_jobs}",
                "transaction.boundary": "${component.boundary}",
            },
            **{"max_tasks": 3, "boundary": "interval"},
        )
        assert connector.config.tasks_max == 3
        assert connector.config.errors_log_enable is False
        assert connector.config.transaction_boundary == "interval"

        with pytest.raises(ValidationError):
            KafkaSourceConnector(
                name=CONNECTOR_NAME,
                config={
                    **connector_config.model_dump(),
                    "transaction.boundary": "${component.boundary}",
                },
                **{"boundary": "invalid"},
            )

    def test_config_provider_reference_in_typed_config_fields(
        self, connector_config: KafkaConnectorConfig
    ) -> None:
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config={
                **connector_config.model_dump(),
                "tasks.max": "${file:/etc/connect/connector.properties:tasks.max}",
                "errors.tolerance": "${env:ERRORS_TOLERANCE}",
            },
        )
        assert connector.config.model_dump()["tasks.max"] == (
            "${file:/etc/connect/connector.properties:tasks.max}"
        )
        assert connector.config.model_dump()["errors.tolerance"] == (
            "${env:ERRORS_TOLERANCE}"
        )

        with pytest.raises(ValidationError):
            KafkaSourceConnector(
                name=CONNECTOR_NAME,
                config={
                    **connector_config.model_dump(),
                    "tasks.max": "${component.max_taks}",
                },
            )

    def test_from_section_raises_exception(
        self,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        with pytest.raises(ValidationError, match="does not support"):
            KafkaSourceConnector(
                name=CONNECTOR_NAME,
                config=connector_config,
                from_=FromSection(
                    topics={
                        TopicName("connector-topic"): FromTopic(
                            type=InputTopicTypes.INPUT
                        ),
                    }
                ),
            )

    async def test_deploy_order(
        self,
        connector: KafkaSourceConnector,
        mocker: MockerFixture,
    ) -> None:
        mock_create_topic = mocker.patch.object(
            get_handlers().topic_handler, "create_topic"
        )

        mock_create_connector = mocker.patch.object(
            get_handlers().connector_handler, "create_connector"
        )

        mock = mocker.AsyncMock()
        mock.attach_mock(mock_create_topic, "mock_create_topic")
        mock.attach_mock(mock_create_connector, "mock_create_connector")
        dry_run = True

        await connector.deploy(dry_run=dry_run)
        assert connector.to
        assert mock.mock_calls == [
            *(
                mocker.call.mock_create_topic(topic, dry_run=dry_run)
                for topic in connector.to.kafka_topics
            ),
            mocker.call.mock_create_connector(
                connector.config, state=None, dry_run=dry_run
            ),
        ]

    @pytest.mark.parametrize(
        "initial_state",
        [None, ConnectorNewState.RUNNING, ConnectorNewState.PAUSED],
    )
    async def test_deploy_initial_state(
        self,
        connector: KafkaSourceConnector,
        initial_state: ConnectorNewState | None,
        mocker: MockerFixture,
    ) -> None:
        mock_create_connector = mocker.patch.object(
            get_handlers().connector_handler, "create_connector"
        )

        connector.state = initial_state
        dry_run = True
        await connector.deploy(dry_run=dry_run)
        assert mock_create_connector.mock_calls == [
            mocker.call(connector.config, state=initial_state, dry_run=dry_run)
        ]

    async def test_destroy(
        self,
        connector: KafkaSourceConnector,
        mocker: MockerFixture,
    ) -> None:
        mock_destroy_connector = mocker.patch.object(
            get_handlers().connector_handler, "destroy_connector"
        )

        await connector.destroy(dry_run=True)

        mock_destroy_connector.assert_called_once_with(
            CONNECTOR_FULL_NAME, dry_run=True
        )

    async def test_reset_when_dry_run_is_true(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_reset_connector = mocker.patch.object(
            get_handlers().connector_handler, "reset_connector"
        )
        dry_run = True
        await connector.reset(dry_run=dry_run)

        mock_destroy.assert_called_once_with(dry_run)
        dry_run_handler_mock.print_helm_diff.assert_not_called()
        mock_reset_connector.assert_called_once_with(connector.config, dry_run=dry_run)

    async def test_reset_when_dry_run_is_false(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_delete_topic = mocker.patch.object(
            get_handlers().topic_handler, "delete_topic"
        )
        mock_reset_connector = mocker.patch.object(
            get_handlers().connector_handler, "reset_connector"
        )

        dry_run = False
        await connector.reset(dry_run)

        mock_reset_connector.assert_called_once_with(connector.config, dry_run=dry_run)
        mock_destroy.assert_called_once_with(dry_run)
        mock_delete_topic.assert_not_called()
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_when_dry_run_is_true(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
    ) -> None:
        await connector.clean(dry_run=True)

        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_when_dry_run_is_false(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_delete_topic = mocker.patch.object(
            get_handlers().topic_handler, "delete_topic"
        )
        mock_reset_connector = mocker.patch.object(
            get_handlers().connector_handler, "reset_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_reset_connector, "mock_reset_connector")
        mock.attach_mock(mock_destroy, "destroy_connector")
        mock.attach_mock(mock_delete_topic, "mock_delete_topic")

        dry_run = False
        await connector.clean(dry_run)

        assert connector.to
        assert mock.mock_calls == [
            mocker.call.mock_reset_connector(connector.config, dry_run=dry_run),
            mocker.call.destroy_connector(dry_run),
            *(
                mocker.call.mock_delete_topic(topic, dry_run=dry_run)
                for topic in connector.to.kafka_topics
            ),
        ]
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_without_to_when_dry_run_is_false(
        self,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
        )
        assert connector.to is None

        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_delete_topic = mocker.patch.object(
            get_handlers().topic_handler, "delete_topic"
        )
        mock_reset_connector = mocker.patch.object(
            get_handlers().connector_handler, "reset_connector"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_reset_connector, "mock_reset_connector")
        mock.attach_mock(mock_destroy, "destroy_connector")
        mock.attach_mock(mock_delete_topic, "mock_delete_topic")

        dry_run = False
        await connector.clean(dry_run)

        assert mock.mock_calls == [
            mocker.call.mock_reset_connector(connector.config, dry_run=dry_run),
            mocker.call.destroy_connector(dry_run),
        ]
        mock_delete_topic.assert_not_called()
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_without_to_when_dry_run_is_true(
        self,
        dry_run_handler_mock: MagicMock,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
        )
        assert connector.to is None

        await connector.clean(dry_run=True)

        dry_run_handler_mock.print_helm_diff.assert_not_called()

    def test_placeholder_in_nested_model(
        self, connector_config: KafkaConnectorConfig
    ) -> None:
        topic_config = TopicConfig.model_validate(
            {"type": "output", "partitions_count": "${component.partitions}"}
        )
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            to=ToSection(topics={TopicName("output-topic"): topic_config}),
            **{"partitions": 3},
        )
        assert connector.to
        assert connector.to.topics[TopicName("output-topic")].partitions_count == 3

        with pytest.raises(ValidationError):
            KafkaSourceConnector(
                name=CONNECTOR_NAME,
                config=connector_config,
                to=ToSection(topics={TopicName("output-topic"): topic_config}),
            )
