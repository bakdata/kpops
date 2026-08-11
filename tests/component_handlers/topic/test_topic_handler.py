import json
import re
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
import structlog
from anyio import Path
from structlog.testing import capture_logs

from kpops.component_handlers.topic.exception import (
    TopicNotFoundException,
    TopicTransactionError,
)
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.component_handlers.topic.model import (
    BrokerConfigResponse,
    TopicConfigResponse,
    TopicResponse,
    TopicSpec,
)
from kpops.components.common.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)
from kpops.utils.colorify import greenify, magentaify
from tests.component_handlers.topic import RESOURCES_PATH

log = structlog.get_logger()


class TestTopicHandler:
    @pytest_asyncio.fixture(autouse=True)
    async def get_topic_response_mock(self) -> MagicMock:
        content = await Path(
            RESOURCES_PATH / "kafka_rest_proxy_responses/get_topic_response.json",
        ).read_text()
        response = json.loads(content)

        content = await Path(
            RESOURCES_PATH / "kafka_rest_proxy_responses/broker_response.json",
        ).read_text()
        broker_response = json.loads(content)

        content = await Path(
            RESOURCES_PATH / "kafka_rest_proxy_responses/topic_config_response.json",
        ).read_text()
        response_topic_config = json.loads(content)

        kafka_rest = AsyncMock()
        kafka_rest.get_topic.return_value = TopicResponse.model_validate(response)
        kafka_rest.get_broker_config.return_value = BrokerConfigResponse.model_validate(
            broker_response
        )
        kafka_rest.get_topic_config.return_value = TopicConfigResponse.model_validate(
            response_topic_config
        )
        return kafka_rest

    @pytest_asyncio.fixture(autouse=True)
    async def get_default_topic_response_mock(self) -> MagicMock:
        content = await Path(
            RESOURCES_PATH
            / "kafka_rest_proxy_responses/get_default_topic_response.json",
        ).read_text()
        response = json.loads(content)

        content = await Path(
            RESOURCES_PATH / "kafka_rest_proxy_responses/broker_response.json",
        ).read_text()
        broker_response = json.loads(content)

        kafka_rest = AsyncMock()
        kafka_rest.get_topic.return_value = TopicResponse.model_validate(response)
        kafka_rest.get_broker_config.return_value = BrokerConfigResponse.model_validate(
            broker_response
        )
        return kafka_rest

    def test_convert_config_values_to_str(self) -> None:
        assert TopicConfig(
            partitions_count=1,
            configs={
                "retention.ms": -1,
                "cleanup.policy": "delete",
                "delete.retention.ms": 123456789,
            },
        ).model_dump() == {
            "configs": {
                "retention.ms": "-1",
                "cleanup.policy": "delete",
                "delete.retention.ms": "123456789",
            },
            "key_schema": None,
            "label": None,
            "partitions_count": 1,
            "replication_factor": None,
            "type": None,
            "value_schema": None,
        }

    async def test_should_call_create_topic_with_dry_run_false(self) -> None:
        kafka_rest = AsyncMock()
        kafka_rest.get_topic.side_effect = TopicNotFoundException()
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        topic_spec = {
            "topic_name": "topic-X",
            "partitions_count": 1,
            "replication_factor": 3,
            "configs": [
                {"name": "cleanup.policy", "value": "compact"},
                {"name": "compression.type", "value": "gzip"},
            ],
        }

        kafka_rest.create_topic.assert_called_once_with(
            TopicSpec.model_validate(topic_spec)
        )
        kafka_rest.__dry_run_topic_creation.assert_not_called()

    async def test_should_call_update_topic_config_when_topic_exists_and_with_dry_run_false(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "delete", "delete.retention.ms": "123456789"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        kafka_rest.batch_alter_topic_config.assert_called_once_with(
            "topic-X",
            [
                {"name": "cleanup.policy", "value": "delete"},
                {"name": "delete.retention.ms", "value": "123456789"},
                {"name": "compression.type", "operation": "DELETE"},
            ],
        )
        kafka_rest.__dry_run_topic_creation.assert_not_called()

    async def test_should_update_topic_config_when_one_config_changed(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock

        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "delete", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        kafka_rest.batch_alter_topic_config.assert_called_once_with(
            "topic-X",
            [{"name": "cleanup.policy", "value": "delete"}],
        )

    async def test_should_not_update_topic_config_when_config_not_changed(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock

        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.create_topic(topic, dry_run=False)

        kafka_rest.batch_alter_topic_config.assert_not_called()
        assert {
            "event": "Config of topic didn't change. Skipping update.",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs

    async def test_should_not_update_topic_config_when_config_not_changed_and_not_ordered(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"compression.type": "gzip", "cleanup.policy": "compact"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.create_topic(topic, dry_run=False)

        kafka_rest.batch_alter_topic_config.assert_not_called()
        assert {
            "event": "Config of topic didn't change. Skipping update.",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs

    async def test_should_call_reset_topic_config_when_topic_exists_dry_run_false_and_topic_configs_change(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock

        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        kafka_rest.batch_alter_topic_config.assert_called_once_with(
            "topic-X",
            [{"name": "compression.type", "operation": "DELETE"}],
        )
        kafka_rest.__dry_run_topic_creation.assert_not_called()

    async def test_should_not_call_create_topics_with_dry_run_true_and_topic_not_exists(
        self,
    ) -> None:
        kafka_rest = MagicMock()
        kafka_rest.get_topic.side_effect = TopicNotFoundException()
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=True)

        kafka_rest.create_topic.assert_not_called()

    async def test_should_print_message_with_dry_run_true_and_topic_not_exists(
        self,
    ) -> None:
        kafka_rest = MagicMock()
        kafka_rest.get_topic.side_effect = TopicNotFoundException()
        kafka_rest.host = "http://localhost:8082"
        kafka_rest.cluster_id = "cluster_1"
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.create_topic(topic, dry_run=True)

        assert {
            "event": greenify(
                "Topic Creation: topic-X does not exist in the cluster. Creating topic."
            ),
            "log_level": "info",
        } in cap_logs

    async def test_should_print_message_if_dry_run_and_topic_exists_with_same_partition_count_and_replication_factor(
        self,
        get_topic_response_mock: MagicMock,
    ) -> None:
        kafka_rest = get_topic_response_mock
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.create_topic(topic, dry_run=True)

        kafka_rest.get_topic_config.assert_called_once()  # dry run requests the config to create the diff
        assert {
            "event": "Topic already exists in cluster.",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Topic partition count did not change. Updating configs.",
            "topic_name": "topic-X",
            "partition_count": 10,
            "log_level": "debug",
        } in cap_logs
        assert {
            "event": "Topic replication factor did not change. Updating configs.",
            "topic_name": "topic-X",
            "replication_factor": 3,
            "log_level": "debug",
        } in cap_logs

    async def test_should_print_message_if_dry_run_and_topic_exists_with_default_partition_count_and_replication_factor(
        self,
        get_default_topic_response_mock: MagicMock,
    ) -> None:
        kafka_rest = get_default_topic_response_mock
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.create_topic(topic, dry_run=True)

        kafka_rest.get_topic_config.assert_called_once()  # dry run requests the config to create the diff
        assert {
            "event": "Config changes for topic",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "\n\x1b[32m+ cleanup.policy: compact\n\x1b[0m\x1b[32m+ compression.type: gzip\n\x1b[0m",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Topic already exists in cluster.",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Topic partition count did not change. Updating configs.",
            "topic_name": "topic-X",
            "partition_count": 1,
            "log_level": "debug",
        } in cap_logs
        assert {
            "event": "Topic replication factor did not change. Updating configs.",
            "topic_name": "topic-X",
            "replication_factor": 1,
            "log_level": "debug",
        } in cap_logs

    async def test_should_exit_if_dry_run_and_topic_exists_different_partition_count(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock

        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=200,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)

        with pytest.raises(
            TopicTransactionError,
            match=re.escape(
                "Topic Creation: partition count of topic topic-X changed! Partitions count of topic topic-X is 10. The given partitions count 200."
            ),
        ):
            await topic_handler.create_topic(topic, dry_run=True)
        kafka_rest.get_topic_config.assert_called_once()  # dry run requests the config to create the diff

    async def test_should_exit_if_dry_run_and_topic_exists_different_replication_factor(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock

        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=300,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)

        with pytest.raises(
            TopicTransactionError,
            match=re.escape(
                "Topic Creation: replication factor of topic topic-X changed! Replication factor of topic topic-X is 3. The given replication count 300."
            ),
        ):
            await topic_handler.create_topic(topic, dry_run=True)
        kafka_rest.get_topic_config.assert_called_once()  # dry run requests the config to create the diff

    async def test_should_log_correct_message_when_delete_existing_topic_dry_run(
        self, get_topic_response_mock: MagicMock
    ) -> None:
        kafka_rest = get_topic_response_mock

        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.delete_topic(topic, dry_run=True)

        kafka_rest.get_topic.assert_called_once_with("topic-X")
        assert {
            "event": magentaify(
                "Topic Deletion: topic topic-X exists in the cluster. Deleting topic."
            ),
            "log_level": "info",
        } in cap_logs

    async def test_should_log_correct_message_when_delete_non_existing_topic_dry_run(
        self,
    ) -> None:
        kafka_rest = MagicMock()
        kafka_rest.get_topic.side_effect = TopicNotFoundException

        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.delete_topic(topic, dry_run=True)

        kafka_rest.get_topic.assert_called_once_with("topic-X")
        assert {
            "event": "Topic does not exist in the cluster and cannot be deleted. Skipping.",
            "topic_name": "topic-X",
            "log_level": "warning",
        } in cap_logs

    async def test_should_call_delete_topic_not_dry_run(self) -> None:
        kafka_rest = AsyncMock()
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.delete_topic(topic, dry_run=False)

        assert kafka_rest.mock_calls == [
            mock.call.get_topic("topic-X"),
            mock.call.delete_topic("topic-X"),
        ]

    async def test_should_print_correct_warning_when_deleting_topic_that_does_not_exists_not_dry_run(
        self,
    ) -> None:
        kafka_rest = MagicMock()
        topic_handler = TopicHandler(kafka_rest=kafka_rest)

        kafka_rest.get_topic.side_effect = TopicNotFoundException()

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        with capture_logs() as cap_logs:
            await topic_handler.delete_topic(topic, dry_run=False)

        kafka_rest.get_topic.assert_called_once_with("topic-X")
        assert {
            "event": "Topic does not exist in the cluster and cannot be deleted. Skipping.",
            "topic_name": "topic-X",
            "log_level": "warning",
        } in cap_logs
