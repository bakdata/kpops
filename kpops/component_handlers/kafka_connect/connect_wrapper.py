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
    ConnectorNewState,
    ConnectorResponse,
    ConnectorStatusResponse,
    CreateConnector,
    KafkaConnectConfigErrorResponse,
    KafkaConnectorConfig,
)

if TYPE_CHECKING:
    from pydantic import AnyHttpUrl

    from kpops.config import KafkaConnectConfig


log = logging.getLogger("KafkaConnectAPI")


@final
class ConnectWrapper:
    """Wraps Kafka Connect APIs."""

    def __init__(self, config: KafkaConnectConfig) -> None:
        self._config: KafkaConnectConfig = config
        self._client = httpx.AsyncClient(
            base_url=str(config.url),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=config.timeout,
        )

    @property
    def url(self) -> AnyHttpUrl:
        return self._config.url

    async def create_connector(
        self,
        connector_config: KafkaConnectorConfig,
        initial_state: ConnectorNewState | None = None,
    ) -> ConnectorResponse:
        """Create a new connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#post--connectors
        :param connector_config: The config of the connector
        :param initial_state: The new state of the connector
        :return: The current connector info if successful.
        """
        payload = CreateConnector(
            config=connector_config,
            initial_state=initial_state,
        )
        response = await self._client.post(
            "/connectors", json=payload.model_dump(exclude_none=True)
        )
        if response.status_code == httpx.codes.CREATED:
            log.info(f"Connector {connector_config.name} created.")
            log.debug(response.json())
            return ConnectorResponse.model_validate(response.json())
        if response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while creating a connector... Retrying..."
            )
            await asyncio.sleep(1)
            return await self.create_connector(connector_config, initial_state)
        raise KafkaConnectError(response)

    async def get_connector(self, connector_name: str) -> ConnectorResponse:
        """Get information about a connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#get--connectors-(string-name)
        :param connector_name: Name of the connector
        :return: Information about the connector.
        """
        response = await self._client.get(f"/connectors/{connector_name}")
        if response.status_code == httpx.codes.OK:
            log.debug(response.json())
            return ConnectorResponse.model_validate(response.json())
        if response.status_code == httpx.codes.NOT_FOUND:
            raise ConnectorNotFoundException
        if response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while getting a connector... Retrying..."
            )
            await asyncio.sleep(1)
            return await self.get_connector(connector_name)
        raise KafkaConnectError(response)

    async def get_connector_status(
        self, connector_name: str
    ) -> ConnectorStatusResponse:
        """Get current status of a connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#get--connectors-(string-name)-status
        :param connector_name: Name of the connector
        :return: Status of the connector.
        """
        response = await self._client.get(f"/connectors/{connector_name}/status")
        if response.status_code == httpx.codes.OK:
            log.debug(response.json())
            return ConnectorStatusResponse.model_validate(response.json())
        if response.status_code == httpx.codes.NOT_FOUND:
            raise ConnectorNotFoundException
        raise KafkaConnectError(response)

    async def pause_connector(self, connector_name: str) -> None:
        """Pause connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#put--connectors-(string-name)-pause
        :param connector_name: Name of the connector
        """
        response = await self._client.put(f"/connectors/{connector_name}/pause")
        if response.status_code != httpx.codes.ACCEPTED:
            raise KafkaConnectError(response)
        log.info(f"Connector {connector_name} paused.")

    async def resume_connector(self, connector_name: str) -> None:
        """Resume connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#put--connectors-(string-name)-resume
        :param connector_name: Name of the connector
        """
        response = await self._client.put(f"/connectors/{connector_name}/resume")
        if response.status_code != httpx.codes.ACCEPTED:
            raise KafkaConnectError(response)
        log.info(f"Connector {connector_name} resumed.")

    async def stop_connector(self, connector_name: str) -> None:
        """Stop connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#put--connectors-(string-name)-stop
        :param connector_name: Name of the connector
        """
        response = await self._client.put(f"/connectors/{connector_name}/stop")
        if response.status_code != httpx.codes.NO_CONTENT:
            raise KafkaConnectError(response)
        log.info(f"Connector {connector_name} stopped.")

    async def update_connector_config(
        self, connector_config: KafkaConnectorConfig
    ) -> ConnectorResponse:
        """Create or update a connector.

        Create a new connector using the given configuration, or update the
        configuration for an existing connector.
        :param connector_config: Configuration parameters for the connector.
        :return: Information about the connector after the change has been made.
        """
        connector_name = connector_config.name

        config_json = connector_config.model_dump()
        response = await self._client.put(
            f"/connectors/{connector_name}/config",
            json=config_json,
        )

        data: dict[str, Any] = response.json()
        if response.status_code == httpx.codes.OK:
            log.info(f"Config for connector {connector_name} updated.")
            log.debug(data)
            return ConnectorResponse.model_validate(data)
        if response.status_code == httpx.codes.CREATED:
            log.info(f"Connector {connector_name} created.")
            log.debug(data)
            return ConnectorResponse.model_validate(data)
        if response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while updating a connector... Retrying..."
            )
            await asyncio.sleep(1)
            return await self.update_connector_config(connector_config)
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
            f"/connector-plugins/{connector_config.class_name}/config/validate",
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
        response = await self._client.delete(f"/connectors/{connector_name}")
        if response.status_code == httpx.codes.NO_CONTENT:
            log.info(f"Connector {connector_name} deleted.")
            return None
        if response.status_code == httpx.codes.NOT_FOUND:
            raise ConnectorNotFoundException
        if response.status_code == httpx.codes.CONFLICT:
            log.warning(
                "Rebalancing in progress while deleting a connector... Retrying..."
            )
            await asyncio.sleep(1)
            return await self.delete_connector(connector_name)
        raise KafkaConnectError(response)
