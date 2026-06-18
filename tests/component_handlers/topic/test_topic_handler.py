import json
import logging
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from anyio import Path
from pytest_mock import MockerFixture

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

log = logging.getLogger()
log.level = logging.DEBUG


class TestTopicHandler:
    @pytest.fixture(autouse=True)
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.handler.log.info")

    @pytest.fixture(autouse=True)
    def log_debug_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.handler.log.debug")

    @pytest.fixture(autouse=True)
    def log_warning_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.handler.log.warning")

    @pytest.fixture(autouse=True)
    def log_error_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.handler.log.error")

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

        wrapper = AsyncMock()
        wrapper.get_topic.return_value = TopicResponse.model_validate(response)
        wrapper.get_broker_config.return_value = BrokerConfigResponse.model_validate(
            broker_response
        )
        wrapper.get_topic_config.return_value = TopicConfigResponse.model_validate(
            response_topic_config
        )
        return wrapper

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

        wrapper = AsyncMock()
        wrapper.get_topic.return_value = TopicResponse.model_validate(response)
        wrapper.get_broker_config.return_value = BrokerConfigResponse.model_validate(
            broker_response
        )
        return wrapper

    def test_convert_config_values_to_str(self):
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

    async def test_should_call_create_topic_with_dry_run_false(self):
        wrapper = AsyncMock()
        wrapper.get_topic.side_effect = TopicNotFoundException()
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

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

        wrapper.create_topic.assert_called_once_with(
            TopicSpec.model_validate(topic_spec)
        )
        wrapper.__dry_run_topic_creation.assert_not_called()

    async def test_should_call_update_topic_config_when_topic_exists_and_with_dry_run_false(
        self, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "delete", "delete.retention.ms": "123456789"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        wrapper.batch_alter_topic_config.assert_called_once_with(
            "topic-X",
            [
                {"name": "cleanup.policy", "value": "delete"},
                {"name": "delete.retention.ms", "value": "123456789"},
                {"name": "compression.type", "operation": "DELETE"},
            ],
        )
        wrapper.__dry_run_topic_creation.assert_not_called()

    async def test_should_update_topic_config_when_one_config_changed(
        self, log_info_mock: MagicMock, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock

        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "delete", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        wrapper.batch_alter_topic_config.assert_called_once_with(
            "topic-X",
            [{"name": "cleanup.policy", "value": "delete"}],
        )

    async def test_should_not_update_topic_config_when_config_not_changed(
        self, log_info_mock: MagicMock, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock

        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        wrapper.batch_alter_topic_config.assert_not_called()
        log_info_mock.assert_called_once_with(
            "Topic Creation: config of topic topic-X didn't change. Skipping update."
        )

    async def test_should_not_update_topic_config_when_config_not_changed_and_not_ordered(
        self, log_info_mock: MagicMock, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"compression.type": "gzip", "cleanup.policy": "compact"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        wrapper.batch_alter_topic_config.assert_not_called()
        log_info_mock.assert_called_once_with(
            "Topic Creation: config of topic topic-X didn't change. Skipping update."
        )

    async def test_should_call_reset_topic_config_when_topic_exists_dry_run_false_and_topic_configs_change(
        self, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock

        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=False)

        wrapper.batch_alter_topic_config.assert_called_once_with(
            "topic-X",
            [{"name": "compression.type", "operation": "DELETE"}],
        )
        wrapper.__dry_run_topic_creation.assert_not_called()

    async def test_should_not_call_create_topics_with_dry_run_true_and_topic_not_exists(
        self,
    ):
        wrapper = MagicMock()
        wrapper.get_topic.side_effect = TopicNotFoundException()
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=True)

        wrapper.create_topic.assert_not_called()

    async def test_should_print_message_with_dry_run_true_and_topic_not_exists(
        self, log_info_mock: MagicMock
    ):
        wrapper = MagicMock()
        wrapper.get_topic.side_effect = TopicNotFoundException()
        wrapper.host = "http://localhost:8082"
        wrapper.cluster_id = "cluster_1"
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=True)

        log_info_mock.assert_called_once_with(
            greenify(
                "Topic Creation: topic-X does not exist in the cluster. Creating topic."
            )
        )

    async def test_should_print_message_if_dry_run_and_topic_exists_with_same_partition_count_and_replication_factor(
        self,
        log_info_mock: MagicMock,
        log_debug_mock: MagicMock,
        get_topic_response_mock: MagicMock,
    ):
        wrapper = get_topic_response_mock
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=True)

        wrapper.get_topic_config.assert_called_once()  # dry run requests the config to create the diff
        assert log_info_mock.mock_calls == [
            mock.call("Topic Creation: topic-X already exists in cluster.")
        ]
        assert log_debug_mock.mock_calls == [
            mock.call("HTTP/1.1 400 Bad Request"),
            mock.call({"Content-Type": "application/json"}),
            mock.call(
                {"error_code": 40002, "message": "Topic 'topic-X' already exists."}
            ),
            mock.call(
                "Topic Creation: partition count of topic topic-X did not change. Current partitions count 10. Updating configs."
            ),
            mock.call(
                "Topic Creation: replication factor of topic topic-X did not change. Current replication factor 3. Updating configs."
            ),
        ]

    async def test_should_print_message_if_dry_run_and_topic_exists_with_default_partition_count_and_replication_factor(
        self,
        log_info_mock: MagicMock,
        log_debug_mock: MagicMock,
        get_default_topic_response_mock: MagicMock,
    ):
        wrapper = get_default_topic_response_mock
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.create_topic(topic, dry_run=True)

        wrapper.get_topic_config.assert_called_once()  # dry run requests the config to create the diff
        assert log_info_mock.mock_calls == [
            mock.call("Config changes for topic topic-X:"),
            mock.call(
                "\n\x1b[32m+ cleanup.policy: compact\n\x1b[0m\x1b[32m+ compression.type: gzip\n\x1b[0m"
            ),
            mock.call("Topic Creation: topic-X already exists in cluster."),
        ]
        assert log_debug_mock.mock_calls == [
            mock.call("HTTP/1.1 400 Bad Request"),
            mock.call({"Content-Type": "application/json"}),
            mock.call(
                {"error_code": 40002, "message": "Topic 'topic-X' already exists."}
            ),
            mock.call(
                "Topic Creation: partition count of topic topic-X did not change. Current partitions count 1. Updating configs."
            ),
            mock.call(
                "Topic Creation: replication factor of topic topic-X did not change. Current replication factor 1. Updating configs."
            ),
        ]

    async def test_should_exit_if_dry_run_and_topic_exists_different_partition_count(
        self, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock

        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=200,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)

        with pytest.raises(
            TopicTransactionError,
            match="Topic Creation: partition count of topic topic-X changed! Partitions count of topic topic-X is 10. The given partitions count 200.",
        ):
            await topic_handler.create_topic(topic, dry_run=True)
        wrapper.get_topic_config.assert_called_once()  # dry run requests the config to create the diff

    async def test_should_exit_if_dry_run_and_topic_exists_different_replication_factor(
        self, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock

        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=300,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)

        with pytest.raises(
            TopicTransactionError,
            match="Topic Creation: replication factor of topic topic-X changed! Replication factor of topic topic-X is 3. The given replication count 300.",
        ):
            await topic_handler.create_topic(topic, dry_run=True)
        wrapper.get_topic_config.assert_called_once()  # dry run requests the config to create the diff

    async def test_should_log_correct_message_when_delete_existing_topic_dry_run(
        self, log_info_mock: MagicMock, get_topic_response_mock: MagicMock
    ):
        wrapper = get_topic_response_mock

        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=10,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.delete_topic(topic, dry_run=True)

        wrapper.get_topic.assert_called_once_with("topic-X")
        log_info_mock.assert_called_once_with(
            magentaify(
                "Topic Deletion: topic topic-X exists in the cluster. Deleting topic."
            )
        )

    async def test_should_log_correct_message_when_delete_non_existing_topic_dry_run(
        self, log_warning_mock: MagicMock
    ):
        wrapper = MagicMock()
        wrapper.get_topic.side_effect = TopicNotFoundException

        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.delete_topic(topic, dry_run=True)

        wrapper.get_topic.assert_called_once_with("topic-X")
        log_warning_mock.assert_called_once_with(
            "Topic Deletion: topic topic-X does not exist in the cluster and cannot be deleted. Skipping."
        )

    async def test_should_call_delete_topic_not_dry_run(self):
        wrapper = AsyncMock()
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.delete_topic(topic, dry_run=False)

        assert wrapper.mock_calls == [
            mock.call.get_topic("topic-X"),
            mock.call.delete_topic("topic-X"),
        ]

    async def test_should_print_correct_warning_when_deleting_topic_that_does_not_exists_not_dry_run(
        self, log_warning_mock: MagicMock
    ):
        wrapper = MagicMock()
        topic_handler = TopicHandler(proxy_wrapper=wrapper)

        wrapper.get_topic.side_effect = TopicNotFoundException()

        topic_config = TopicConfig(
            type=OutputTopicTypes.OUTPUT,
            partitions_count=1,
            replication_factor=3,
            configs={"cleanup.policy": "compact", "compression.type": "gzip"},
        )
        topic = KafkaTopic(name="topic-X", config=topic_config)
        await topic_handler.delete_topic(topic, dry_run=False)

        wrapper.get_topic.assert_called_once_with("topic-X")
        log_warning_mock.assert_called_once_with(
            "Topic Deletion: topic topic-X does not exist in the cluster and cannot be deleted. Skipping."
        )
