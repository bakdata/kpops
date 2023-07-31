import asyncio
import logging
from typing import Any

import httpx

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
        self._client = httpx.AsyncClient(base_url=host)
        self._host: str = host

    @property
    def host(self) -> str:
        return self._host

    async def create_connector(
        self, connector_name: str, kafka_connect_config: KafkaConnectConfig
    ) -> KafkaConnectResponse:
        """
        Creates a new connector
        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#post--connectors
        :param connector_name: The name of the connector
        :param kafka_connect_config: The config of the connector
        :return: The current connector info if successful
        """
        config_json = kafka_connect_config.dict(exclude_none=True)
        connect_data = {"name": connector_name, "config": config_json}

        response = await self._client.post(
            url=f"/connectors", headers=HEADERS, json=connect_data
        )
        if response.status_code == httpx.codes.CREATED:
            log.info(f"Connector {connector_name} created.")
            log.debug(response.json())
            return KafkaConnectResponse(**response.json())
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while creating a connector... Retrying..."
            )
            await asyncio.sleep(1)
            await self.create_connector(connector_name, kafka_connect_config)
        raise KafkaConnectError(response)

    async def get_connector(self, connector_name: str) -> KafkaConnectResponse:
        """
        Get information about the connector.
        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#get--connectors-(string-name)
        :param connector_name: Nameof the crated connector
        :return: Information about the connector
        """
        response = await self._client.get(
            url=f"/connectors/{connector_name}", headers=HEADERS
        )
        if response.status_code == httpx.codes.OK:
            log.info(f"Connector {connector_name} exists.")
            log.debug(response.json())
            return KafkaConnectResponse(**response.json())
        elif response.status_code == httpx.codes.NOT_FOUND:
            log.info(f"The named connector {connector_name} does not exists.")
            raise ConnectorNotFoundException()
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while getting a connector... Retrying..."
            )
            await asyncio.sleep(1)
            await self.get_connector(connector_name)
        raise KafkaConnectError(response)

    async def update_connector_config(
        self, connector_name: str, kafka_connect_config: KafkaConnectConfig
    ) -> KafkaConnectResponse:
        """
        Create a new connector using the given configuration, or update the configuration for an existing connector.
        :param connector_name: Name of the created connector
        :param kafka_connect_config: Configuration parameters for the connector.
        :return: Information about the connector after the change has been made.
        """
        config_json = kafka_connect_config.dict(exclude_none=True)
        response = await self._client.put(
            url=f"/connectors/{connector_name}/config",
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
            await asyncio.sleep(1)
            await self.update_connector_config(connector_name, kafka_connect_config)
        raise KafkaConnectError(response)

    @classmethod
    def get_connector_config(
        cls, connector_name: str, config: KafkaConnectConfig
    ) -> dict[str, Any]:
        connector_config = config.dict(exclude_none=True)
        if (name := connector_config.get("name")) and name != connector_name:
            raise ValueError("Connector name should be the same as component name")
        connector_config["name"] = connector_name
        return connector_config

    async def validate_connector_config(
        self, connector_name: str, kafka_connect_config: KafkaConnectConfig
    ) -> list[str]:
        """
        Validate connector config using the given configuration
        :param connector_name: Name of the created connector
        :param kafka_connect_config: Configuration parameters for the connector.
        :return:
        """

        config_json = self.get_connector_config(connector_name, kafka_connect_config)
        connector_class = ConnectWrapper.get_connector_class_name(config_json)

        response = await self._client.put(
            url=f"/connector-plugins/{connector_class}/config/validate",
            headers=HEADERS,
            json=config_json,
        )

        if response.status_code == httpx.codes.OK:
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

    async def delete_connector(self, connector_name: str) -> None:
        """
        Deletes a connector, halting all tasks and deleting its configuration.
        API Reference:https://docs.confluent.io/platform/current/connect/references/restapi.html#delete--connectors-(string-name)-
        """
        response = await self._client.delete(
            url=f"/connectors/{connector_name}", headers=HEADERS
        )
        if response.status_code == httpx.codes.NO_CONTENT:
            log.info(f"Connector {connector_name} deleted.")
            return
        elif response.status_code == httpx.codes.NOT_FOUND:
            log.info(f"The named connector {connector_name} does not exists.")
            raise ConnectorNotFoundException()
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while deleting a connector... Retrying..."
            )
            await asyncio.sleep(1)
            await self.delete_connector(connector_name)
        raise KafkaConnectError(response)

    @staticmethod
    def get_connector_class_name(config_json: dict[str, str]) -> str:
        task_class = config_json["connector.class"]
        return task_class.split(".")[-1]
