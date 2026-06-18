import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from anyio import Path
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
from tests.component_handlers.topic import RESOURCES_PATH

HEADERS = {"Content-Type": "application/json"}
DEFAULT_HOST = "http://localhost:8082"


class TestProxyWrapper:
    @pytest.fixture(autouse=True)
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.proxy_wrapper.log.info")

    @pytest.fixture(autouse=True)
    def log_debug_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.topic.proxy_wrapper.log.debug")

    @pytest_asyncio.fixture()
    async def proxy_wrapper(self, httpx_mock: HTTPXMock) -> ProxyWrapper:
        config = KpopsConfig()  # pyright: ignore[reportCallIssue]
        proxy_wrapper = ProxyWrapper(config.kafka_rest)
        content = await Path(
            RESOURCES_PATH / "kafka_rest_proxy_responses" / "cluster-info.json",
        ).read_text()
        cluster_response = json.loads(content)

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters",
            json=cluster_response,
            status_code=httpx.codes.OK,
        )
        assert proxy_wrapper.url == AnyHttpUrl(DEFAULT_HOST)
        assert proxy_wrapper.cluster_id == "cluster-1"
        return proxy_wrapper

    @patch("httpx.AsyncClient.post")
    async def test_should_create_topic_with_all_topic_configuration(
        self, mock_post: AsyncMock, proxy_wrapper: ProxyWrapper
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
            await proxy_wrapper.create_topic(
                topic_spec=TopicSpec.model_validate(topic_spec)
            )

        mock_post.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{proxy_wrapper.cluster_id}/topics",
            headers=HEADERS,
            json=topic_spec,
        )

    @patch("httpx.AsyncClient.post")
    async def test_should_create_topic_with_no_configuration(
        self, mock_post: AsyncMock, proxy_wrapper: ProxyWrapper
    ):
        topic_spec: dict[str, Any] = {"topic_name": "topic-X"}

        with pytest.raises(KafkaRestProxyError):
            await proxy_wrapper.create_topic(
                topic_spec=TopicSpec.model_validate(topic_spec)
            )

        mock_post.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{proxy_wrapper.cluster_id}/topics",
            headers=HEADERS,
            json=topic_spec,
        )

    @patch("httpx.AsyncClient.get")
    async def test_should_call_get_topic(
        self, mock_get: AsyncMock, proxy_wrapper: ProxyWrapper
    ):
        topic_name = "topic-X"

        with pytest.raises(KafkaRestProxyError):
            await proxy_wrapper.get_topic(topic_name=topic_name)

        mock_get.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{proxy_wrapper.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )

    @patch("httpx.AsyncClient.post")
    async def test_should_call_batch_alter_topic_config(
        self, mock_put: AsyncMock, proxy_wrapper: ProxyWrapper
    ):
        topic_name = "topic-X"

        with pytest.raises(KafkaRestProxyError):
            await proxy_wrapper.batch_alter_topic_config(
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

    @patch("httpx.AsyncClient.delete")
    async def test_should_call_delete_topic(
        self, mock_delete: AsyncMock, proxy_wrapper: ProxyWrapper
    ):
        topic_name = "topic-X"

        with pytest.raises(KafkaRestProxyError):
            await proxy_wrapper.delete_topic(topic_name=topic_name)

        mock_delete.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{proxy_wrapper.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )

    @patch("httpx.AsyncClient.get")
    async def test_should_call_get_broker_config(
        self, mock_get: AsyncMock, proxy_wrapper: ProxyWrapper
    ):
        with pytest.raises(KafkaRestProxyError):
            await proxy_wrapper.get_broker_config()

        mock_get.assert_called_with(
            url=f"{DEFAULT_HOST}/v3/clusters/{proxy_wrapper.cluster_id}/brokers/-/configs",
            headers=HEADERS,
        )

    async def test_should_log_topic_creation(
        self,
        proxy_wrapper: ProxyWrapper,
        log_info_mock: MagicMock,
        httpx_mock: HTTPXMock,
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
            status_code=httpx.codes.CREATED,
        )
        await proxy_wrapper.create_topic(
            topic_spec=TopicSpec.model_validate(topic_spec)
        )
        log_info_mock.assert_called_once_with("Topic topic-X created.")

    async def test_should_log_topic_deletion(
        self,
        proxy_wrapper: ProxyWrapper,
        log_info_mock: MagicMock,
        httpx_mock: HTTPXMock,
    ):
        topic_name = "topic-X"

        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=httpx.codes.NO_CONTENT,
        )
        await proxy_wrapper.delete_topic(topic_name=topic_name)
        log_info_mock.assert_called_once_with("Topic topic-X deleted.")

    async def test_should_get_topic(
        self,
        proxy_wrapper: ProxyWrapper,
        log_debug_mock: MagicMock,
        httpx_mock: HTTPXMock,
    ):
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
        topic_response = TopicResponse.model_validate(res)

        topic_name = "topic-X"

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=httpx.codes.OK,
            json=res,
        )

        get_topic_response = await proxy_wrapper.get_topic(topic_name=topic_name)

        log_debug_mock.assert_any_call("Topic topic-X found.")
        assert get_topic_response == topic_response

    async def test_should_rais_topic_not_found_exception_get_topic(
        self,
        proxy_wrapper: ProxyWrapper,
        log_debug_mock: MagicMock,
        httpx_mock: HTTPXMock,
    ):
        topic_name = "topic-X"

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=httpx.codes.NOT_FOUND,
            json={
                "error_code": 40403,
                "message": "This server does not host this topic-partition.",
            },
        )
        with pytest.raises(TopicNotFoundException):
            await proxy_wrapper.get_topic(topic_name=topic_name)
        log_debug_mock.assert_any_call("Topic topic-X not found.")

    async def test_should_log_reset_default_topic_config_when_deleted(
        self,
        proxy_wrapper: ProxyWrapper,
        log_info_mock: MagicMock,
        httpx_mock: HTTPXMock,
    ):
        topic_name = "topic-X"
        config_name = "cleanup.policy"

        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}/configs:alter",
            headers=HEADERS,
            json={"data": [{"name": config_name, "operation": "DELETE"}]},
            status_code=httpx.codes.NO_CONTENT,
        )

        await proxy_wrapper.batch_alter_topic_config(
            topic_name=topic_name,
            json_body=[{"name": config_name, "operation": "DELETE"}],
        )

        log_info_mock.assert_called_once_with(
            f"Config of topic {topic_name} was altered."
        )
