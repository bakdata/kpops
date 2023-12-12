import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import AnyHttpUrl
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from kpops.component_handlers.topic.exception import (
    KafkaRestProxyError,
    TopicNotFoundException,
)
from kpops.component_handlers.topic.model import TopicResponse, TopicSpec
from kpops.component_handlers.topic.proxy_wrapper import ProxyWrapper
from kpops.config import KpopsConfig

HEADERS = {"Content-Type": "application/json"}
DEFAULT_HOST = "http://localhost:8082"
DEFAULTS_PATH = Path(__file__).parent.parent / "resources"


class TestProxyWrapper:
    @pytest.fixture(autouse=True)
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.proxy_wrapper.log.info")

    @pytest.fixture(autouse=True)
    def log_debug_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.proxy_wrapper.log.debug")

    @pytest.fixture(autouse=True)
    def _setup(self, httpx_mock: HTTPXMock):
        config = KpopsConfig(defaults_path=DEFAULTS_PATH)
        self.proxy_wrapper = ProxyWrapper(config.kafka_rest)

        with Path(
            DEFAULTS_PATH / "kafka_rest_proxy_responses" / "cluster-info.json",
        ).open() as f:
            cluster_response = json.load(f)

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters",
            json=cluster_response,
            status_code=200,
        )
        assert self.proxy_wrapper.url == AnyHttpUrl(DEFAULT_HOST)
        assert self.proxy_wrapper.cluster_id == "cluster-1"

    @patch("httpx.post")
    def test_should_create_topic_with_all_topic_configuration(
        self, mock_post: MagicMock
    ):
        topic_spec = {
            "topic_name": "topic-X",
            "partitions_count": 1,
            "replication_factor": 3,
            "configs": [
                {"name": "cleanup.policy", "value": "compact"},
                {"name": "compression.type", "value": "gzip"},
            ],
        }

        with pytest.raises(KafkaRestProxyError):
            self.proxy_wrapper.create_topic(topic_spec=TopicSpec(**topic_spec))

        mock_post.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{self.proxy_wrapper.cluster_id}/topics",
            headers=HEADERS,
            json=topic_spec,
        )

    @patch("httpx.post")
    def test_should_create_topic_with_no_configuration(self, mock_post: MagicMock):
        topic_spec: dict[str, Any] = {"topic_name": "topic-X"}

        with pytest.raises(KafkaRestProxyError):
            self.proxy_wrapper.create_topic(topic_spec=TopicSpec(**topic_spec))

        mock_post.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{self.proxy_wrapper.cluster_id}/topics",
            headers=HEADERS,
            json=topic_spec,
        )

    @patch("httpx.get")
    def test_should_call_get_topic(self, mock_get: MagicMock):
        topic_name = "topic-X"

        with pytest.raises(KafkaRestProxyError):
            self.proxy_wrapper.get_topic(topic_name=topic_name)

        mock_get.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{self.proxy_wrapper.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )

    @patch("httpx.post")
    def test_should_call_batch_alter_topic_config(self, mock_put: MagicMock):
        topic_name = "topic-X"

        with pytest.raises(KafkaRestProxyError):
            self.proxy_wrapper.batch_alter_topic_config(
                topic_name=topic_name,
                json_body=[
                    {"name": "cleanup.policy", "operation": "DELETE"},
                    {"name": "compression.type", "value": "gzip"},
                ],
            )

        mock_put.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}/configs:alter",
            headers=HEADERS,
            json={
                "data": [
                    {"name": "cleanup.policy", "operation": "DELETE"},
                    {"name": "compression.type", "value": "gzip"},
                ]
            },
        )

    @patch("httpx.delete")
    def test_should_call_delete_topic(self, mock_delete: MagicMock):
        topic_name = "topic-X"

        with pytest.raises(KafkaRestProxyError):
            self.proxy_wrapper.delete_topic(topic_name=topic_name)

        mock_delete.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{self.proxy_wrapper.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )

    @patch("httpx.get")
    def test_should_call_get_broker_config(self, mock_get: MagicMock):
        with pytest.raises(KafkaRestProxyError):
            self.proxy_wrapper.get_broker_config()

        mock_get.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{self.proxy_wrapper.cluster_id}/brokers/-/configs",
            headers=HEADERS,
        )

    def test_should_log_topic_creation(
        self, log_info_mock: MagicMock, httpx_mock: HTTPXMock
    ):
        topic_spec = {
            "topic_name": "topic-X",
            "partitions_count": 1,
            "replication_factor": 3,
            "configs": [
                {"name": "cleanup.policy", "value": "compact"},
                {"name": "compression.type", "value": "gzip"},
            ],
        }

        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics",
            json=topic_spec,
            headers=HEADERS,
            status_code=201,
        )
        self.proxy_wrapper.create_topic(topic_spec=TopicSpec(**topic_spec))
        log_info_mock.assert_called_once_with("Topic topic-X created.")

    def test_should_log_topic_deletion(
        self, log_info_mock: MagicMock, httpx_mock: HTTPXMock
    ):
        topic_name = "topic-X"

        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=204,
        )
        self.proxy_wrapper.delete_topic(topic_name=topic_name)
        log_info_mock.assert_called_once_with("Topic topic-X deleted.")

    def test_should_get_topic(self, log_debug_mock: MagicMock, httpx_mock: HTTPXMock):
        res = {
            "kind": "KafkaTopic",
            "metadata": {
                "self": "https://pkc-00000.region.provider.confluent.cloud/kafka/v3/clusters/cluster-1/topics/topic-1",
                "resource_name": "crn:///kafka=cluster-1/topic=topic-1",
            },
            "cluster_id": "cluster-1",
            "topic_name": "topic-1",
            "is_internal": "false",
            "replication_factor": 3,
            "partitions_count": 1,
            "partitions": {"related": ""},
            "configs": {"related": ""},
            "partition_reassignments": {"related": ""},
        }
        topic_response = TopicResponse(**res)

        topic_name = "topic-X"

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=200,
            json=res,
        )

        get_topic_response = self.proxy_wrapper.get_topic(topic_name=topic_name)

        log_debug_mock.assert_any_call("Topic topic-X found.")
        assert get_topic_response == topic_response

    def test_should_rais_topic_not_found_exception_get_topic(
        self, log_debug_mock: MagicMock, httpx_mock: HTTPXMock
    ):
        topic_name = "topic-X"

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=404,
            json={
                "error_code": 40403,
                "message": "This server does not host this topic-partition.",
            },
        )
        with pytest.raises(TopicNotFoundException):
            self.proxy_wrapper.get_topic(topic_name=topic_name)
        log_debug_mock.assert_any_call("Topic topic-X not found.")

    def test_should_log_reset_default_topic_config_when_deleted(
        self, log_info_mock: MagicMock, httpx_mock: HTTPXMock
    ):
        topic_name = "topic-X"
        config_name = "cleanup.policy"

        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}/configs:alter",
            headers=HEADERS,
            json={"data": [{"name": config_name, "operation": "DELETE"}]},
            status_code=204,
        )

        self.proxy_wrapper.batch_alter_topic_config(
            topic_name=topic_name,
            json_body=[{"name": config_name, "operation": "DELETE"}],
        )

        log_info_mock.assert_called_once_with(
            f"Config of topic {topic_name} was altered."
        )
