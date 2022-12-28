import logging
import time
from time import sleep

import requests

from kpops.component_handlers.kafka_connect.exception import (
    ConnectorNotFoundException,
    KafkaConnectError,
)
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectConfig,
    KafkaConnectConfigErrorResponse,
    KafkaConnectResponse,
)

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

log = logging.getLogger("KafkaConnectAPI")


class ConnectWrapper:
    """
    Wraps Kafka Connect APIs
    """

    def __init__(self, host: str | None):
        if not host:
            error_message = (
                "The Kafka Connect host is not set. Please set the host in the config."
            )
            log.error(error_message)
            raise RuntimeError(error_message)
        self._host: str = host

    @property
    def host(self) -> str:
        return self._host

    def create_connector(
        self, connector_name: str, kafka_connect_config: KafkaConnectConfig
    ) -> KafkaConnectResponse:
        """
        Creates a new connector
        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#post--connectors
        :param connector_name: The name of the connector
        :param kafka_connect_config: The config of the connector
        :return: The current connector info if successful
        """
        config_json = kafka_connect_config.dict(exclude_none=True, exclude_unset=True)
        connect_data = {"name": connector_name, "config": config_json}
        response = requests.post(
            url=f"{self._host}/connectors", headers=HEADERS, json=connect_data
        )
        if response.status_code == requests.status_codes.codes.created:
            log.info(f"Connector {connector_name} created.")
            log.debug(response.json())
            return KafkaConnectResponse(**response.json())
        elif response.status_code == requests.status_codes.codes.conflict:
            log.warning(
                "Rebalancing in progress while creating a connector... Retrying..."
            )
            time.sleep(1)
            self.create_connector(connector_name, kafka_connect_config)
        raise KafkaConnectError(response)

    def get_connector(self, connector_name: str) -> KafkaConnectResponse:
        """
        Get information about the connector.
        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#get--connectors-(string-name)
        :param connector_name: Nameof the crated connector
        :return: Information about the connector
        """
        response = requests.get(
            url=f"{self._host}/connectors/{connector_name}", headers=HEADERS
        )
        if response.status_code == requests.status_codes.codes.ok:
            log.info(f"Connector {connector_name} exists.")
            log.debug(response.json())
            return KafkaConnectResponse(**response.json())
        elif response.status_code == requests.status_codes.codes.not_found:
            log.info(f"The named connector {connector_name} does not exists.")
            raise ConnectorNotFoundException()
        elif response.status_code == requests.status_codes.codes.conflict:
            log.warning(
                "Rebalancing in progress while getting a connector... Retrying..."
            )
            sleep(1)
            self.get_connector(connector_name)
        raise KafkaConnectError(response)

    def update_connector_config(
        self, connector_name: str, kafka_connect_config: KafkaConnectConfig
    ) -> KafkaConnectResponse:
        """
        Create a new connector using the given configuration, or update the configuration for an existing connector.
        :param connector_name: Name of the created connector
        :param kafka_connect_config: Configuration parameters for the connector.
        :return: Information about the connector after the change has been made.
        """
        config_json = kafka_connect_config.dict(exclude_none=True, exclude_unset=True)
        response = requests.put(
            url=f"{self._host}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=config_json,
        )
        data: dict = response.json()
        if response.status_code == requests.status_codes.codes.ok:
            log.info(f"Config for connector {connector_name} updated.")
            log.debug(data)
            return KafkaConnectResponse(**data)
        if response.status_code == requests.status_codes.codes.created:
            log.info(f"Connector {connector_name} created.")
            log.debug(data)
            return KafkaConnectResponse(**data)
        elif response.status_code == requests.status_codes.codes.conflict:
            log.warning(
                "Rebalancing in progress while updating a connector... Retrying..."
            )
            sleep(1)
            self.update_connector_config(connector_name, kafka_connect_config)
        raise KafkaConnectError(response)

    def validate_connector_config(
        self, kafka_connect_config: KafkaConnectConfig
    ) -> list[str]:
        """
        Validate connector config using the given configuration
        :param connector_name: Name of the created connector
        :param kafka_connect_config: Configuration parameters for the connector.
        :return:
        """
        config_json = kafka_connect_config.dict(exclude_none=True, exclude_unset=True)
        connector_class = ConnectWrapper.get_connector_class_name(config_json)

        response = requests.put(
            url=f"{self._host}/connector-plugins/{connector_class}/config/validate",
            headers=HEADERS,
            json=config_json,
        )

        if response.status_code == requests.status_codes.codes.ok:
            kafka_connect_error_response = KafkaConnectConfigErrorResponse(
                **response.json()
            )

            errors = []
            if kafka_connect_error_response.error_count > 0:
                for config in kafka_connect_error_response.configs:
                    if len(config.value.errors) > 0:
                        for error in config.value.errors:
                            errors.append(
                                f"Found error for field {config.value.name}: {error}"
                            )
            return errors
        raise KafkaConnectError(response)

    def delete_connector(self, connector_name: str) -> None:
        """
        Deletes a connector, halting all tasks and deleting its configuration.
        API Reference:https://docs.confluent.io/platform/current/connect/references/restapi.html#delete--connectors-(string-name)-
        """
        response = requests.delete(
            url=f"{self._host}/connectors/{connector_name}", headers=HEADERS
        )
        if response.status_code == requests.status_codes.codes.no_content:
            log.info(f"Connector {connector_name} deleted.")
            return
        elif response.status_code == requests.status_codes.codes.not_found:
            log.info(f"The named connector {connector_name} does not exists.")
            raise ConnectorNotFoundException()
        elif response.status_code == requests.status_codes.codes.conflict:
            log.warning(
                "Rebalancing in progress while deleting a connector... Retrying..."
            )
            sleep(1)
            self.delete_connector(connector_name)
        raise KafkaConnectError(response)

    @staticmethod
    def get_connector_class_name(config_json: dict[str, str]) -> str:
        task_class = config_json["connector.class"]
        return task_class.split(".")[-1]
