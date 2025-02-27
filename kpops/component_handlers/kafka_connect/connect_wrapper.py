from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, final

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

if TYPE_CHECKING:
    from pydantic import AnyHttpUrl

    from kpops.config import KafkaConnectConfig

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

log = logging.getLogger("KafkaConnectAPI")


@final
class ConnectWrapper:
    """Wraps Kafka Connect APIs."""

    def __init__(self, config: KafkaConnectConfig) -> None:
        self._config: KafkaConnectConfig = config
        self._client = httpx.AsyncClient(timeout=config.timeout)

    @property
    def url(self) -> AnyHttpUrl:
        return self._config.url

    async def create_connector(
        self, connector_config: KafkaConnectorConfig
    ) -> KafkaConnectResponse:
        """Create a new connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#post--connectors
        :param connector_config: The config of the connector
        :return: The current connector info if successful.
        """
        config_json: dict[str, Any] = connector_config.model_dump()
        connect_data: dict[str, Any] = {
            "name": connector_config.name,
            "config": config_json,
        }
        response = await self._client.post(
            url=f"{self.url}connectors", headers=HEADERS, json=connect_data
        )
        if response.status_code == httpx.codes.CREATED:
            log.info(f"Connector {connector_config.name} created.")
            log.debug(response.json())
            return KafkaConnectResponse.model_validate(response.json())
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while creating a connector... Retrying..."
            )

            await asyncio.sleep(1)
            await self.create_connector(connector_config)

        raise KafkaConnectError(response)

    async def get_connector(self, connector_name: str | None) -> KafkaConnectResponse:
        """Get information about the connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#get--connectors-(string-name)
        :param connector_name: Nameof the crated connector
        :return: Information about the connector.
        """
        if connector_name is None:
            msg = "Connector name not set"
            raise Exception(msg)
        response = await self._client.get(
            url=f"{self.url}connectors/{connector_name}", headers=HEADERS
        )
        if response.status_code == httpx.codes.OK:
            log.info(f"Connector {connector_name} exists.")
            log.debug(response.json())
            return KafkaConnectResponse.model_validate(response.json())
        elif response.status_code == httpx.codes.NOT_FOUND:
            log.info(f"The named connector {connector_name} does not exists.")
            raise ConnectorNotFoundException
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while getting a connector... Retrying..."
            )
            await asyncio.sleep(1)
            await self.get_connector(connector_name)
        raise KafkaConnectError(response)

    async def update_connector_config(
        self, connector_config: KafkaConnectorConfig
    ) -> KafkaConnectResponse:
        """Create or update a connector.

        Create a new connector using the given configuration, or update the
        configuration for an existing connector.
        :param connector_config: Configuration parameters for the connector.
        :return: Information about the connector after the change has been made.
        """
        connector_name = connector_config.name

        config_json = connector_config.model_dump()
        response = await self._client.put(
            url=f"{self.url}connectors/{connector_name}/config",
            headers=HEADERS,
            json=config_json,
        )

        data: dict[str, Any] = response.json()
        if response.status_code == httpx.codes.OK:
            log.info(f"Config for connector {connector_name} updated.")
            log.debug(data)
            return KafkaConnectResponse.model_validate(data)
        if response.status_code == httpx.codes.CREATED:
            log.info(f"Connector {connector_name} created.")
            log.debug(data)
            return KafkaConnectResponse.model_validate(data)
        elif response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while updating a connector... Retrying..."
            )
            await asyncio.sleep(1)
            await self.update_connector_config(connector_config)
        raise KafkaConnectError(response)

    async def validate_connector_config(
        self, connector_config: KafkaConnectorConfig
    ) -> list[str]:
        """Validate connector config using the given configuration.

        :param connector_config: Configuration parameters for the connector.
        :raises KafkaConnectError: Kafka Connect error
        :return: List of all found errors
        """
        response = await self._client.put(
            url=f"{self.url}connector-plugins/{connector_config.class_name}/config/validate",
            headers=HEADERS,
            json=connector_config.model_dump(),
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

    async def delete_connector(self, connector_name: str) -> None:
        """Delete a connector, halting all tasks and deleting its configuration.

        API Reference:
            https://docs.confluent.io/platform/current/connect/references/restapi.html#delete--connectors-(string-name)-.
        :param connector_name: Configuration parameters for the connector.
        :raises ConnectorNotFoundException: Connector not found
        """
        response = await self._client.delete(
            url=f"{self.url}connectors/{connector_name}", headers=HEADERS
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
            await asyncio.sleep(1)
            await self.delete_connector(connector_name)
        raise KafkaConnectError(response)
