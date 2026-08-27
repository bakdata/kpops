import json
from typing import Any

import httpx2
import pytest
import pytest_asyncio
from anyio import Path
from pydantic import AnyHttpUrl
from pytest_httpx2 import HTTPXMock
from structlog.testing import capture_logs

from kpops.component_handlers.topic.exception import (
    KafkaRestProxyConnectionError,
    KafkaRestProxyError,
    KafkaRestProxyException,
    TopicNotFoundException,
)
from kpops.component_handlers.topic.kafka_rest import KafkaRest
from kpops.component_handlers.topic.model import TopicResponse, TopicSpec
from kpops.config import KpopsConfig
from tests.component_handlers.topic import RESOURCES_PATH

HEADERS = {"Content-Type": "application/json"}
DEFAULT_HOST = "http://localhost:8082"


class TestKafkaRest:
    @pytest_asyncio.fixture()
    async def kafka_rest(self, httpx_mock: HTTPXMock) -> KafkaRest:
        config = KpopsConfig()
        kafka_rest = KafkaRest(config.kafka_rest)
        content = await Path(
            RESOURCES_PATH / "kafka_rest_proxy_responses" / "cluster-info.json",
        ).read_text()
        cluster_response = json.loads(content)

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters",
            json=cluster_response,
            status_code=httpx2.codes.OK,
        )
        assert kafka_rest.url == AnyHttpUrl(DEFAULT_HOST)
        assert kafka_rest.cluster_id == "cluster-1"
        return kafka_rest

    async def test_should_create_topic_with_all_topic_configuration(
        self, kafka_rest: KafkaRest, httpx_mock: HTTPXMock
    ) -> None:
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
            url=f"{DEFAULT_HOST}/v3/clusters/{kafka_rest.cluster_id}/topics",
            status_code=httpx2.codes.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(KafkaRestProxyError):
            await kafka_rest.create_topic(
                topic_spec=TopicSpec.model_validate(topic_spec)
            )

        request = httpx_mock.get_requests()[-1]
        assert json.loads(request.content) == topic_spec

    async def test_should_create_topic_with_no_configuration(
        self, kafka_rest: KafkaRest, httpx_mock: HTTPXMock
    ) -> None:
        topic_spec: dict[str, Any] = {"topic_name": "topic-X"}
        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/v3/clusters/{kafka_rest.cluster_id}/topics",
            status_code=httpx2.codes.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(KafkaRestProxyError):
            await kafka_rest.create_topic(
                topic_spec=TopicSpec.model_validate(topic_spec)
            )

        request = httpx_mock.get_requests()[-1]
        assert json.loads(request.content) == topic_spec

    async def test_should_call_get_topic(
        self, kafka_rest: KafkaRest, httpx_mock: HTTPXMock
    ) -> None:
        topic_name = "topic-X"
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters/{kafka_rest.cluster_id}/topics/{topic_name}",
            status_code=httpx2.codes.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(KafkaRestProxyError):
            await kafka_rest.get_topic(topic_name=topic_name)

    async def test_should_call_batch_alter_topic_config(
        self, kafka_rest: KafkaRest, httpx_mock: HTTPXMock
    ) -> None:
        topic_name = "topic-X"
        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}/configs:alter",
            status_code=httpx2.codes.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(KafkaRestProxyError):
            await kafka_rest.batch_alter_topic_config(
                topic_name=topic_name,
                json_body=[
                    {"name": "cleanup.policy", "operation": "DELETE"},
                    {"name": "compression.type", "value": "gzip"},
                ],
            )

        request = httpx_mock.get_requests()[-1]
        assert json.loads(request.content) == {
            "data": [
                {"name": "cleanup.policy", "operation": "DELETE"},
                {"name": "compression.type", "value": "gzip"},
            ]
        }

    async def test_should_call_delete_topic(
        self, kafka_rest: KafkaRest, httpx_mock: HTTPXMock
    ) -> None:
        topic_name = "topic-X"
        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/v3/clusters/{kafka_rest.cluster_id}/topics/{topic_name}",
            status_code=httpx2.codes.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(KafkaRestProxyError):
            await kafka_rest.delete_topic(topic_name=topic_name)

    async def test_should_call_get_broker_config(
        self, kafka_rest: KafkaRest, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters/{kafka_rest.cluster_id}/brokers/-/configs",
            status_code=httpx2.codes.INTERNAL_SERVER_ERROR,
        )

        with pytest.raises(KafkaRestProxyError):
            await kafka_rest.get_broker_config()

    async def test_should_raise_connection_error_when_service_unreachable(
        self, kafka_rest: KafkaRest, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_exception(httpx2.ConnectError("Connection refused"))

        with pytest.raises(KafkaRestProxyConnectionError, match="Connection refused"):
            await kafka_rest.get_broker_config()

    @pytest.mark.parametrize(
        "exception",
        [
            TopicNotFoundException(),
            KafkaRestProxyConnectionError(url="http://x", cause=ValueError("x")),
        ],
    )
    def test_umbrella_exception_catches_all_kafka_rest_proxy_errors(
        self, exception: Exception
    ) -> None:
        assert isinstance(exception, KafkaRestProxyException)

    def test_umbrella_exception_catches_http_response_error(self) -> None:
        request = httpx2.Request("GET", "http://x")
        response = httpx2.Response(500, json={"message": "oops"}, request=request)
        error = KafkaRestProxyError(response)
        assert isinstance(error, KafkaRestProxyException)

    async def test_should_log_topic_creation(
        self,
        kafka_rest: KafkaRest,
        httpx_mock: HTTPXMock,
    ) -> None:
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
            status_code=httpx2.codes.CREATED,
        )
        with capture_logs() as cap_logs:
            await kafka_rest.create_topic(
                topic_spec=TopicSpec.model_validate(topic_spec)
            )
        assert {
            "event": "Topic created.",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs

    async def test_should_log_topic_deletion(
        self,
        kafka_rest: KafkaRest,
        httpx_mock: HTTPXMock,
    ) -> None:
        topic_name = "topic-X"

        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=httpx2.codes.NO_CONTENT,
        )
        with capture_logs() as cap_logs:
            await kafka_rest.delete_topic(topic_name=topic_name)
        assert {
            "event": "Topic deleted.",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs

    async def test_should_get_topic(
        self,
        kafka_rest: KafkaRest,
        httpx_mock: HTTPXMock,
    ) -> None:
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
            status_code=httpx2.codes.OK,
            json=res,
        )

        with capture_logs() as cap_logs:
            get_topic_response = await kafka_rest.get_topic(topic_name=topic_name)

        assert {
            "event": "Topic found.",
            "topic_name": "topic-X",
            "log_level": "debug",
        } in cap_logs
        assert get_topic_response == topic_response

    async def test_should_rais_topic_not_found_exception_get_topic(
        self,
        kafka_rest: KafkaRest,
        httpx_mock: HTTPXMock,
    ) -> None:
        topic_name = "topic-X"

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}",
            headers=HEADERS,
            status_code=httpx2.codes.NOT_FOUND,
            json={
                "error_code": 40403,
                "message": "This server does not host this topic-partition.",
            },
        )
        with capture_logs() as cap_logs, pytest.raises(TopicNotFoundException):
            await kafka_rest.get_topic(topic_name=topic_name)
        assert {
            "event": "Topic not found.",
            "topic_name": "topic-X",
            "log_level": "debug",
        } in cap_logs

    async def test_should_log_reset_default_topic_config_when_deleted(
        self,
        kafka_rest: KafkaRest,
        httpx_mock: HTTPXMock,
    ) -> None:
        topic_name = "topic-X"
        config_name = "cleanup.policy"

        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/v3/clusters/cluster-1/topics/{topic_name}/configs:alter",
            headers=HEADERS,
            json={"data": [{"name": config_name, "operation": "DELETE"}]},
            status_code=httpx2.codes.NO_CONTENT,
        )

        with capture_logs() as cap_logs:
            await kafka_rest.batch_alter_topic_config(
                topic_name=topic_name,
                json_body=[{"name": config_name, "operation": "DELETE"}],
            )

        assert {
            "event": "Config of topic was altered.",
            "topic_name": "topic-X",
            "log_level": "info",
        } in cap_logs
