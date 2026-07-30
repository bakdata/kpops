from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, final

import httpx
import structlog

from kpops.component_handlers.topic.exception import (
    KafkaRestProxyConnectionError,
    KafkaRestProxyError,
    TopicNotFoundException,
)
from kpops.component_handlers.topic.model import (
    BrokerConfigResponse,
    TopicConfigResponse,
    TopicResponse,
    TopicSpec,
)
from kpops.utils.logging import bound_service_context

if TYPE_CHECKING:
    from pydantic import AnyHttpUrl

    from kpops.config import KafkaRestConfig

log = structlog.get_logger("KafkaRestProxy")

HEADERS = {"Content-Type": "application/json"}


@final
class ProxyWrapper:
    """Wraps Kafka REST Proxy APIs."""

    def __init__(self, config: KafkaRestConfig) -> None:
        self._config: KafkaRestConfig = config
        self._client = httpx.AsyncClient(timeout=config.timeout)
        self._sync_client = httpx.Client(timeout=config.timeout)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Send a request, translating transport failures into a KafkaRestProxyConnectionError."""
        try:
            return await self._client.request(method, url, headers=headers, json=json)
        except httpx.TransportError as ex:
            raise KafkaRestProxyConnectionError(url=url, cause=ex) from ex

    def _sync_request(self, method: str, url: str) -> httpx.Response:
        """Sync counterpart to `_request`."""
        try:
            return self._sync_client.request(method, url)
        except httpx.TransportError as ex:
            raise KafkaRestProxyConnectionError(url=url, cause=ex) from ex

    @cached_property
    def cluster_id(self) -> str:
        """Get the Kafka cluster ID by sending a request to Kafka REST proxy.

        More information about the cluster ID can be found here:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#cluster-v3.

        Currently both Kafka and Kafka REST Proxy are only aware of the Kafka cluster pointed at by the
        bootstrap.servers configuration. Therefore, only one Kafka cluster will be returned.

        :raises KafkaRestProxyConnectionError: Connection to Kafka REST Proxy failed
        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: The Kafka cluster ID.
        """
        with bound_service_context(service="Kafka REST Proxy", url=str(self.url)):
            response = self._sync_request("GET", url=f"{self._config.url!s}v3/clusters")

            if response.status_code == httpx.codes.OK:
                cluster_information = response.json()
                return cluster_information["data"][0]["cluster_id"]

            raise KafkaRestProxyError(response)

    @property
    def url(self) -> AnyHttpUrl:
        return self._config.url

    async def create_topic(self, topic_spec: TopicSpec) -> None:
        """Create a topic.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#post--clusters-cluster_id-topics

        :param topic_spec: The topic specification.
        :raises KafkaRestProxyConnectionError: Connection to Kafka REST Proxy failed
        :raises KafkaRestProxyError: Kafka REST proxy error
        """
        with bound_service_context(service="Kafka REST Proxy", url=str(self.url)):
            response = await self._request(
                "POST",
                url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics",
                headers=HEADERS,
                json=topic_spec.model_dump(exclude_none=True),
            )

            if response.status_code == httpx.codes.CREATED:
                log.info("Topic created.", topic_name=topic_spec.topic_name)
                return

            raise KafkaRestProxyError(response)

    async def delete_topic(self, topic_name: str) -> None:
        """Delete a topic.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#delete--clusters-cluster_id-topics-topic_name

        :param topic_name: Name of the topic.
        :raises KafkaRestProxyConnectionError: Connection to Kafka REST Proxy failed
        :raises KafkaRestProxyError: Kafka REST proxy error
        """
        with bound_service_context(service="Kafka REST Proxy", url=str(self.url)):
            response = await self._request(
                "DELETE",
                url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}",
                headers=HEADERS,
            )

            if response.status_code == httpx.codes.NO_CONTENT:
                log.info("Topic deleted.", topic_name=topic_name)
                return

            raise KafkaRestProxyError(response)

    async def get_topic(self, topic_name: str) -> TopicResponse:
        """Return the topic with the given topic_name.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#get--clusters-cluster_id-topics-topic_name
        :param topic_name: The topic name.
        :raises TopicNotFoundException: Topic not found
        :raises KafkaRestProxyConnectionError: Connection to Kafka REST Proxy failed
        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: Response of the get topic API.
        """
        with bound_service_context(service="Kafka REST Proxy", url=str(self.url)):
            response = await self._request(
                "GET",
                url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}",
                headers=HEADERS,
            )

            if response.status_code == httpx.codes.OK:
                log.debug("Topic found.", topic_name=topic_name)
                return TopicResponse.model_validate(response.json())

            elif (
                response.status_code == httpx.codes.NOT_FOUND
                and response.json()["error_code"] == 40403
            ):
                log.debug("Topic not found.", topic_name=topic_name)
                raise TopicNotFoundException

            raise KafkaRestProxyError(response)

    async def get_topic_config(self, topic_name: str) -> TopicConfigResponse:
        """Return the config with the given topic_name.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#acl-v3
        :param topic_name: The topic name.
        :raises TopicNotFoundException: Topic not found
        :raises KafkaRestProxyConnectionError: Connection to Kafka REST Proxy failed
        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: The topic configuration.
        """
        with bound_service_context(service="Kafka REST Proxy", url=str(self.url)):
            response = await self._request(
                "GET",
                url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}/configs",
                headers=HEADERS,
            )

            if response.status_code == httpx.codes.OK:
                log.debug("Configs found.", topic_name=topic_name)
                return TopicConfigResponse.model_validate(response.json())

            elif (
                response.status_code == httpx.codes.NOT_FOUND
                and response.json()["error_code"] == 40403
            ):
                log.debug("Configs not found.", topic_name=topic_name)
                raise TopicNotFoundException

            raise KafkaRestProxyError(response)

    async def batch_alter_topic_config(
        self, topic_name: str, json_body: list[dict[str, Any]]
    ) -> None:
        """Reset config of given config_name param to the default value on the Kafka server.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#post--clusters-cluster_id-topics-topic_name-configs-alter

        :param topic_name: The topic name.
        :param config_name: The configuration parameter name.
        :raises KafkaRestProxyConnectionError: Connection to Kafka REST Proxy failed
        :raises KafkaRestProxyError: Kafka REST proxy error
        """
        with bound_service_context(service="Kafka REST Proxy", url=str(self.url)):
            response = await self._request(
                "POST",
                url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}/configs:alter",
                headers=HEADERS,
                json={"data": json_body},
            )

            if response.status_code == httpx.codes.NO_CONTENT:
                log.info("Config of topic was altered.", topic_name=topic_name)
                return

            raise KafkaRestProxyError(response)

    async def get_broker_config(self) -> BrokerConfigResponse:
        """Return the list of configuration parameters for all the brokers in the given Kafka cluster.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#get--clusters-cluster_id-brokers---configs

        :raises KafkaRestProxyConnectionError: Connection to Kafka REST Proxy failed
        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: The broker configuration.
        """
        with bound_service_context(service="Kafka REST Proxy", url=str(self.url)):
            response = await self._request(
                "GET",
                url=f"{self.url!s}v3/clusters/{self.cluster_id}/brokers/-/configs",
                headers=HEADERS,
            )

            if response.status_code == httpx.codes.OK:
                log.debug("Broker configs found.")
                return BrokerConfigResponse.model_validate(response.json())

            raise KafkaRestProxyError(response)
