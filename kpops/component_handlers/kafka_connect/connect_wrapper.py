import logging
import time
from time import sleep

import httpx

from kpops.component_handlers.kafka_connect.exception import (
    ConnectorNotFoundException,
    KafkaConnectError,
)
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectConfigErrorResponse,
    KafkaConnectorConfig,
    KafkaConnectResponse,
)

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

log = logging.getLogger("KafkaConnectAPI")


class ConnectWrapper:
    """Wraps Kafka Connect APIs."""

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
        self, connector_config: KafkaConnectorConfig
    ) -> KafkaConnectResponse:
        """Create a new connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#post--connectors
        :param connector_config: The config of the connector
        :return: The current connector info if successful.
        """
        config_json = connector_config.dict()
        connect_data = {"name": connector_config.name, "config": config_json}
        response = httpx.post(
            url=f"{self._host}/connectors", headers=HEADERS, json=connect_data
        )
        if response.status_code == httpx.codes.CREATED:
            log.info(f"Connector {connector_config.name} created.")
            log.debug(response.json())
            return KafkaConnectResponse(**response.json())
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while creating a connector... Retrying..."
            )
            time.sleep(1)
            self.create_connector(connector_config)
        raise KafkaConnectError(response)

    def get_connector(self, connector_name: str) -> KafkaConnectResponse:
        """Get information about the connector.

        API Reference:
        https://docs.confluent.io/platform/current/connect/references/restapi.html#get--connectors-(string-name)

        :param connector_name: Nameof the crated connector
        :return: Information about the connector.
        """
        response = httpx.get(
            url=f"{self._host}/connectors/{connector_name}", headers=HEADERS
        )
        if response.status_code == httpx.codes.OK:
            log.info(f"Connector {connector_name} exists.")
            log.debug(response.json())
            return KafkaConnectResponse(**response.json())
        elif response.status_code == httpx.codes.NOT_FOUND:
            log.info(f"The named connector {connector_name} does not exists.")
            raise ConnectorNotFoundException
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while getting a connector... Retrying..."
            )
            sleep(1)
            self.get_connector(connector_name)
        raise KafkaConnectError(response)

    def update_connector_config(
        self, connector_config: KafkaConnectorConfig
    ) -> KafkaConnectResponse:
        """Create or update a connector.

        Create a new connector using the given configuration,or update the
        configuration for an existing connector.

        :param connector_config: Configuration parameters for the connector.
        :return: Information about the connector after the change has been made.
        """
        connector_name = connector_config.name
        config_json = connector_config.dict()
        response = httpx.put(
            url=f"{self._host}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=config_json,
        )
        data: dict = response.json()
        if response.status_code == httpx.codes.OK:
            log.info(f"Config for connector {connector_name} updated.")
            log.debug(data)
            return KafkaConnectResponse(**data)
        if response.status_code == httpx.codes.CREATED:
            log.info(f"Connector {connector_name} created.")
            log.debug(data)
            return KafkaConnectResponse(**data)
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while updating a connector... Retrying..."
            )
            sleep(1)
            self.update_connector_config(connector_config)
        raise KafkaConnectError(response)

    def validate_connector_config(
        self, connector_config: KafkaConnectorConfig
    ) -> list[str]:
        """Validate connector config using the given configuration.

        :param connector_config: Configuration parameters for the connector.
        :raises KafkaConnectError: Kafka Konnect error
        :return: List of all found errors
        """
        response = httpx.put(
            url=f"{self._host}/connector-plugins/{connector_config.class_name}/config/validate",
            headers=HEADERS,
            json=connector_config.dict(),
        )

        if response.status_code == httpx.codes.OK:
            kafka_connect_error_response = KafkaConnectConfigErrorResponse(
                **response.json()
            )

            errors: list[str] = []
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
        """Delete a connector, halting all tasks and deleting its configuration.

        API Reference:
            https://docs.confluent.io/platform/current/connect/references/restapi.html#delete--connectors-(string-name)-.
        :param connector_name: Configuration parameters for the connector.
        :raises ConnectorNotFoundException: Connector not found
        """
        response = httpx.delete(
            url=f"{self._host}/connectors/{connector_name}", headers=HEADERS
        )
        if response.status_code == httpx.codes.NO_CONTENT:
            log.info(f"Connector {connector_name} deleted.")
            return
        elif response.status_code == httpx.codes.NOT_FOUND:
            log.info(f"The named connector {connector_name} does not exists.")
            raise ConnectorNotFoundException
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while deleting a connector... Retrying..."
            )
            sleep(1)
            self.delete_connector(connector_name)
        raise KafkaConnectError(response)
