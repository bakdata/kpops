from __future__ import annotations

import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any, final

import httpx

from kpops.component_handlers.topic.exception import (
    KafkaRestProxyError,
    TopicNotFoundException,
)
from kpops.component_handlers.topic.model import (
    BrokerConfigResponse,
    TopicConfigResponse,
    TopicResponse,
    TopicSpec,
)

if TYPE_CHECKING:
    from pydantic import AnyHttpUrl

    from kpops.config import KafkaRestConfig

log = logging.getLogger("KafkaRestProxy")

HEADERS = {"Content-Type": "application/json"}


@final
class ProxyWrapper:
    """Wraps Kafka REST Proxy APIs."""

    def __init__(self, config: KafkaRestConfig) -> None:
        self._config: KafkaRestConfig = config
        self._client = httpx.AsyncClient(timeout=config.timeout)
        self._sync_client = httpx.Client(timeout=config.timeout)

    @cached_property
    def cluster_id(self) -> str:
        """Get the Kafka cluster ID by sending a request to Kafka REST proxy.

        More information about the cluster ID can be found here:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#cluster-v3.

        Currently both Kafka and Kafka REST Proxy are only aware of the Kafka cluster pointed at by the
        bootstrap.servers configuration. Therefore, only one Kafka cluster will be returned.

        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: The Kafka cluster ID.
        """
        response = self._sync_client.get(url=f"{self._config.url!s}v3/clusters")

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
        :raises KafkaRestProxyError: Kafka REST proxy error
        """
        response = await self._client.post(
            url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics",
            headers=HEADERS,
            json=topic_spec.model_dump(exclude_none=True),
        )

        if response.status_code == httpx.codes.CREATED:
            log.info(f"Topic {topic_spec.topic_name} created.")
            log.debug(response.json())
            return

        raise KafkaRestProxyError(response)

    async def delete_topic(self, topic_name: str) -> None:
        """Delete a topic.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#delete--clusters-cluster_id-topics-topic_name

        :param topic_name: Name of the topic.
        :raises KafkaRestProxyError: Kafka REST proxy error
        """
        response = await self._client.delete(
            url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )

        if response.status_code == httpx.codes.NO_CONTENT:
            log.info(f"Topic {topic_name} deleted.")
            return

        raise KafkaRestProxyError(response)

    async def get_topic(self, topic_name: str) -> TopicResponse:
        """Return the topic with the given topic_name.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#get--clusters-cluster_id-topics-topic_name
        :param topic_name: The topic name.
        :raises TopicNotFoundException: Topic not found
        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: Response of the get topic API.
        """
        response = await self._client.get(
            url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )

        if response.status_code == httpx.codes.OK:
            log.debug(f"Topic {topic_name} found.")
            log.debug(response.json())
            return TopicResponse.model_validate(response.json())

        elif (
            response.status_code == httpx.codes.NOT_FOUND
            and response.json()["error_code"] == 40403
        ):
            log.debug(f"Topic {topic_name} not found.")
            log.debug(response.json())
            raise TopicNotFoundException

        raise KafkaRestProxyError(response)

    async def get_topic_config(self, topic_name: str) -> TopicConfigResponse:
        """Return the config with the given topic_name.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#acl-v3
        :param topic_name: The topic name.
        :raises TopicNotFoundException: Topic not found
        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: The topic configuration.
        """
        response = await self._client.get(
            url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}/configs",
            headers=HEADERS,
        )

        if response.status_code == httpx.codes.OK:
            log.debug(f"Configs for {topic_name} found.")
            log.debug(response.json())
            return TopicConfigResponse.model_validate(response.json())

        elif (
            response.status_code == httpx.codes.NOT_FOUND
            and response.json()["error_code"] == 40403
        ):
            log.debug(f"Configs for {topic_name} not found.")
            log.debug(response.json())
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
        :raises KafkaRestProxyError: Kafka REST proxy error
        """
        response = await self._client.post(
            url=f"{self.url!s}v3/clusters/{self.cluster_id}/topics/{topic_name}/configs:alter",
            headers=HEADERS,
            json={"data": json_body},
        )

        if response.status_code == httpx.codes.NO_CONTENT:
            log.info(f"Config of topic {topic_name} was altered.")
            return

        raise KafkaRestProxyError(response)

    async def get_broker_config(self) -> BrokerConfigResponse:
        """Return the list of configuration parameters for all the brokers in the given Kafka cluster.

        API Reference:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#get--clusters-cluster_id-brokers---configs

        :raises KafkaRestProxyError: Kafka REST proxy error
        :return: The broker configuration.
        """
        response = await self._client.get(
            url=f"{self.url!s}v3/clusters/{self.cluster_id}/brokers/-/configs",
            headers=HEADERS,
        )

        if response.status_code == httpx.codes.OK:
            log.debug("Broker configs found.")
            log.debug(response.json())
            return BrokerConfigResponse.model_validate(response.json())

        raise KafkaRestProxyError(response)
