import logging
from functools import cached_property

import requests

from kpops.cli.pipeline_config import PipelineConfig
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

log = logging.getLogger("KafkaRestProxy")

HEADERS = {"Content-Type": "application/json"}


class ProxyWrapper:
    """
    Wraps Kafka REST Proxy APIs
    """

    def __init__(self, pipeline_config: PipelineConfig) -> None:
        if not pipeline_config.kafka_rest_host:
            raise ValueError(
                "The Kafka REST Proxy host is not set. Please set the host in the config.yaml using the kafka_rest_host property or set the environemt variable KPOPS_REST_PROXY_HOST."
            )

        self._host = pipeline_config.kafka_rest_host

    @cached_property
    def cluster_id(self) -> str:
        """
        Gets the Kafka cluster ID by sending a requests to Kafka REST proxy.
        More information about the cluster ID can be found here:
        https://docs.confluent.io/platform/current/kafka-rest/api.html#cluster-v3

        Currently both Kafka and Kafka REST Proxy are only aware of the Kafka cluster pointed at by the
        bootstrap.servers configuration. Therefore, only one Kafka cluster will be returned.
        :return: The Kafka cluster ID.
        """
        response = requests.get(url=f"{self._host}/v3/clusters")
        if response.status_code == requests.status_codes.codes.ok:
            cluster_information = response.json()
            return cluster_information["data"][0]["cluster_id"]

        raise KafkaRestProxyError(response)

    @property
    def host(self) -> str:
        return self._host

    def create_topic(self, topic_spec: TopicSpec) -> None:
        """
        Creates a topic.
        API Reference: https://docs.confluent.io/platform/current/kafka-rest/api.html#post--clusters-cluster_id-topics
        :param topic_spec: The topic specification.
        """
        response = requests.post(
            url=f"{self._host}/v3/clusters/{self.cluster_id}/topics",
            headers=HEADERS,
            json=topic_spec.dict(exclude_unset=True, exclude_none=True),
        )
        if response.status_code == requests.status_codes.codes.created:
            log.info(f"Topic {topic_spec.topic_name} created.")
            log.debug(response.json())
            return

        raise KafkaRestProxyError(response)

    def delete_topic(self, topic_name: str) -> None:
        """
        Deletes a topic
        API Reference: https://docs.confluent.io/platform/current/kafka-rest/api.html#delete--clusters-cluster_id-topics-topic_name
        :param topic_name: Name of the topic
        """
        response = requests.delete(
            url=f"{self.host}/v3/clusters/{self.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )
        if response.status_code == requests.status_codes.codes.no_content:
            log.info(f"Topic {topic_name} deleted.")
            return

        raise KafkaRestProxyError(response)

    def get_topic(self, topic_name: str) -> TopicResponse:
        """
        Returns the topic with the given topic_name.
        API Reference: https://docs.confluent.io/platform/current/kafka-rest/api.html#get--clusters-cluster_id-topics-topic_name
        :param topic_name: The topic name.
        :return: Response of the get topic API
        """
        response = requests.get(
            url=f"{self.host}/v3/clusters/{self.cluster_id}/topics/{topic_name}",
            headers=HEADERS,
        )
        if response.status_code == requests.status_codes.codes.ok:
            log.debug(f"Topic {topic_name} found.")
            log.debug(response.json())
            return TopicResponse(**response.json())

        elif (
            response.status_code == requests.status_codes.codes.not_found
            and response.json()["error_code"] == 40403
        ):
            log.debug(f"Topic {topic_name} not found.")
            log.debug(response.json())
            raise TopicNotFoundException()

        raise KafkaRestProxyError(response)

    def get_topic_config(self, topic_name: str) -> TopicConfigResponse:
        """
        Return the config with the given topic_name.
        API Reference: https://docs.confluent.io/platform/current/kafka-rest/api.html#acl-v3
        :param topic_name: The topic name.
        :return: The topic configuration.
        """
        response = requests.get(
            url=f"{self.host}/v3/clusters/{self.cluster_id}/topics/{topic_name}/configs",
            headers=HEADERS,
        )

        if response.status_code == requests.status_codes.codes.ok:
            log.debug(f"Configs for {topic_name} found.")
            log.debug(response.json())
            return TopicConfigResponse(**response.json())

        elif (
            response.status_code == requests.status_codes.codes.not_found
            and response.json()["error_code"] == 40403
        ):
            log.debug(f"Configs for {topic_name} not found.")
            log.debug(response.json())
            raise TopicNotFoundException()

        raise KafkaRestProxyError(response)

    def batch_alter_topic_config(self, topic_name: str, json_body: list[dict]) -> None:
        """
        Reset config of given config_name param to the default value on the kafka server.
        API Reference: https://docs.confluent.io/platform/current/kafka-rest/api.html#post--clusters-cluster_id-topics-topic_name-configs-alter
        :param topic_name: The topic name.
        :param config_name: The configuration parameter name.
        """
        response = requests.post(
            url=f"{self.host}/v3/clusters/{self.cluster_id}/topics/{topic_name}/configs:alter",
            headers=HEADERS,
            json={"data": json_body},
        )
        if response.status_code == requests.status_codes.codes.no_content:
            log.info(f"Config of topic {topic_name} was altered.")
            return

        raise KafkaRestProxyError(response)

    def get_broker_config(self) -> BrokerConfigResponse:
        """
        Return the list of configuration parameters for all the brokers in the given Kafka cluster.
        API Reference: https://docs.confluent.io/platform/current/kafka-rest/api.html#get--clusters-cluster_id-brokers---configs
        :return: The broker configuration.
        """
        response = requests.get(
            url=f"{self.host}/v3/clusters/{self.cluster_id}/brokers/-/configs",
            headers=HEADERS,
        )

        if response.status_code == requests.status_codes.codes.ok:
            log.debug("Broker configs found.")
            log.debug(response.json())
            return BrokerConfigResponse(**response.json())

        raise KafkaRestProxyError(response)
