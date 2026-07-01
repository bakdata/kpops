from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from kpops.component_handlers import get_handlers
from kpops.component_handlers.kafka_connect.model import (
    ConnectorNewState,
    KafkaConnectorConfig,
    KafkaConnectorType,
)
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
            offset_topic=OFFSETS_TOPIC,
        )

    def test_from_section_raises_exception(
        self,
        connector_config: KafkaConnectorConfig,
    ):
        with pytest.raises(NotImplementedError):
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
    ):
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
    ):
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
    ):
        assert get_handlers().connector_handler

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
    ):
        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_reset_connector = mocker.patch.object(
            get_handlers().connector_handler, "reset_connector"
        )
        dry_run = True
        await connector.reset(dry_run=dry_run)

        mock_destroy.assert_not_called()
        dry_run_handler_mock.print_helm_diff.assert_not_called()
        mock_reset_connector.assert_called_once_with(
            CONNECTOR_FULL_NAME, dry_run=dry_run
        )

    async def test_reset_when_dry_run_is_false(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ):
        mock_destroy = mocker.patch.object(connector, "destroy")
        mock_delete_topic = mocker.patch.object(
            get_handlers().topic_handler, "delete_topic"
        )
        mock_reset_connector = mocker.patch.object(
            get_handlers().connector_handler, "reset_connector"
        )

        dry_run = False
        await connector.reset(dry_run)

        mock_reset_connector.assert_called_once_with(
            CONNECTOR_FULL_NAME, dry_run=dry_run
        )
        mock_destroy.assert_not_called()
        mock_delete_topic.assert_not_called()
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_when_dry_run_is_true(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
    ):
        await connector.clean(dry_run=True)

        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_when_dry_run_is_false(
        self,
        connector: KafkaSourceConnector,
        dry_run_handler_mock: MagicMock,
        mocker: MockerFixture,
    ):
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
            mocker.call.mock_reset_connector(CONNECTOR_FULL_NAME, dry_run=dry_run),
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
    ):
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            offset_topic=OFFSETS_TOPIC,
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
            mocker.call.mock_reset_connector(CONNECTOR_FULL_NAME, dry_run=dry_run),
            mocker.call.destroy_connector(dry_run),
        ]
        mock_delete_topic.assert_not_called()
        dry_run_handler_mock.print_helm_diff.assert_not_called()

    async def test_clean_without_to_when_dry_run_is_true(
        self,
        dry_run_handler_mock: MagicMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaSourceConnector(
            name=CONNECTOR_NAME,
            config=connector_config,
            offset_topic=OFFSETS_TOPIC,
        )
        assert connector.to is None

        assert get_handlers().connector_handler

        await connector.clean(dry_run=True)

        dry_run_handler_mock.print_helm_diff.assert_not_called()
