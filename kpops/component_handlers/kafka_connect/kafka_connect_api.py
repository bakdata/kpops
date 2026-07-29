from __future__ import annotations

import asyncio
import logging
from contextlib import suppress
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
class KafkaConnect:
    """Wraps Kafka Connect REST API."""

    def __init__(self, config: KafkaConnectConfig) -> None:
        self._config: KafkaConnectConfig = config
        self._client = httpx.AsyncClient(
            base_url=str(config.url),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=config.timeout,
            event_hooks={
                "request": [self._log_request],
                "response": [self._log_response],
            },
        )

    @property
    def url(self) -> AnyHttpUrl:
        return self._config.url

    @staticmethod
    async def _log_request(request: httpx.Request) -> None:
        """Log an outgoing request."""
        log.debug(f"{request.method} {request.url}")
        if request.content:
            log.debug(request.content.decode())

    @staticmethod
    async def _log_response(response: httpx.Response) -> None:
        """Log an incoming response."""
        await response.aread()
        log.debug(
            f"{response.http_version} {response.status_code} {response.reason_phrase}"
        )
        with suppress(ValueError):
            log.debug(response.json())

    async def request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> httpx.Response | None:
        """Send an HTTP request to Kafka Connect, or preview it in dry-run mode.

        :param method: The HTTP method
        :param endpoint: The endpoint path, relative to the Kafka Connect base URL.
        :param json: Optional JSON payload for the request body.
        :param dry_run: Whether to log the request instead of sending it.
        :return: The HTTP response, or None if dry run.
        """
        request = self._client.build_request(method, endpoint, json=json)
        if dry_run:
            await self._log_request(request)
            return None
        return await self._client.send(request)

    async def create_connector(
        self,
        connector_config: KafkaConnectorConfig,
        initial_state: ConnectorNewState | None = None,
        *,
        dry_run: bool = False,
    ) -> ConnectorResponse | None:
        """Create a new connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#post--connectors
        :param connector_config: The config of the connector
        :param initial_state: The new state of the connector
        :param dry_run: Whether to log the request instead of sending it.
        :return: The current connector info if successful, None if dry run.
        """
        payload = CreateConnector(
            config=connector_config,
            initial_state=initial_state,
        )
        json = payload.model_dump(exclude_none=True)
        response = await self.request("POST", "/connectors", json=json, dry_run=dry_run)
        if response is None:
            return None
        if response.status_code == httpx.codes.CREATED.value:
            log.info(f"Connector {connector_config.name} created.")
            return ConnectorResponse.model_validate_json(response.content)
        if response.status_code == httpx.codes.CONFLICT.value:
            log.warning(
                "Rebalancing in progress while creating a connector... Retrying..."
            )
            await asyncio.sleep(1)
            return await self.create_connector(
                connector_config, initial_state, dry_run=dry_run
            )
        raise KafkaConnectError(response)

    async def get_connector(self, connector_name: str) -> ConnectorResponse:
        """Get information about a connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#get--connectors-(string-name)
        :param connector_name: Name of the connector
        :return: Information about the connector.
        """
        response = await self.request("GET", f"/connectors/{connector_name}")
        assert response is not None
        if response.status_code == httpx.codes.OK.value:
            return ConnectorResponse.model_validate_json(response.content)
        if response.status_code == httpx.codes.NOT_FOUND.value:
            raise ConnectorNotFoundException
        if response.status_code == httpx.codes.CONFLICT.value:
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
        response = await self.request("GET", f"/connectors/{connector_name}/status")
        assert response is not None
        if response.status_code == httpx.codes.OK.value:
            return ConnectorStatusResponse.model_validate_json(response.content)
        if response.status_code == httpx.codes.NOT_FOUND.value:
            raise ConnectorNotFoundException
        raise KafkaConnectError(response)

    async def pause_connector(
        self, connector_name: str, *, dry_run: bool = False
    ) -> None:
        """Pause connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#put--connectors-(string-name)-pause
        :param connector_name: Name of the connector
        :param dry_run: Whether to log the request instead of sending it.
        """
        response = await self.request(
            "PUT", f"/connectors/{connector_name}/pause", dry_run=dry_run
        )
        if response is None:
            return
        if response.status_code != httpx.codes.ACCEPTED.value:
            raise KafkaConnectError(response)
        log.info(f"Connector {connector_name} paused.")

    async def resume_connector(
        self, connector_name: str, *, dry_run: bool = False
    ) -> None:
        """Resume connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#put--connectors-(string-name)-resume
        :param connector_name: Name of the connector
        :param dry_run: Whether to log the request instead of sending it.
        """
        response = await self.request(
            "PUT", f"/connectors/{connector_name}/resume", dry_run=dry_run
        )
        if response is None:
            return
        if response.status_code != httpx.codes.ACCEPTED.value:
            raise KafkaConnectError(response)
        log.info(f"Connector {connector_name} resumed.")

    async def stop_connector(
        self, connector_name: str, *, dry_run: bool = False
    ) -> None:
        """Stop connector.

        API Reference: https://docs.confluent.io/platform/current/connect/references/restapi.html#put--connectors-(string-name)-stop
        :param connector_name: Name of the connector
        :param dry_run: Whether to log the request instead of sending it.
        """
        response = await self.request(
            "PUT", f"/connectors/{connector_name}/stop", dry_run=dry_run
        )
        if response is None:
            return
        if response.status_code != httpx.codes.NO_CONTENT.value:
            raise KafkaConnectError(response)
        log.info(f"Connector {connector_name} stopped.")

    async def update_connector_config(
        self, connector_config: KafkaConnectorConfig, *, dry_run: bool = False
    ) -> ConnectorResponse | None:
        """Create or update a connector.

        Create a new connector using the given configuration, or update the
        configuration for an existing connector.
        :param connector_config: Configuration parameters for the connector.
        :param dry_run: Whether to log the request instead of sending it.
        :return: Information about the connector after the change has been made,
            None if dry run.
        """
        connector_name = connector_config.name
        response = await self.request(
            "PUT",
            f"/connectors/{connector_name}/config",
            json=connector_config.model_dump(),
            dry_run=dry_run,
        )
        if response is None:
            return None

        data: dict[str, Any] = response.json()
        if response.status_code == httpx.codes.OK.value:
            log.info(f"Config for connector {connector_name} updated.")
            return ConnectorResponse.model_validate(data)
        if response.status_code == httpx.codes.CREATED.value:
            log.info(f"Connector {connector_name} created.")
            return ConnectorResponse.model_validate(data)
        if response.status_code == httpx.codes.CONFLICT.value:
            log.warning(
                "Rebalancing in progress while updating a connector... Retrying..."
            )
            await asyncio.sleep(1)
            return await self.update_connector_config(connector_config, dry_run=dry_run)
        raise KafkaConnectError(response)

    async def validate_connector_config(
        self, connector_config: KafkaConnectorConfig
    ) -> list[str]:
        """Validate connector config using the given configuration.

        :param connector_config: Configuration parameters for the connector.
        :raises KafkaConnectError: Kafka Connect error
        :return: List of all found errors
        """
        response = await self.request(
            "PUT",
            f"/connector-plugins/{connector_config.class_name}/config/validate",
            json=connector_config.model_dump(),
        )
        assert response is not None

        if response.status_code == httpx.codes.OK.value:
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

    async def delete_connector(
        self, connector_name: str, *, dry_run: bool = False
    ) -> None:
        """Delete a connector, halting all tasks and deleting its configuration.

        API Reference:
            https://docs.confluent.io/platform/current/connect/references/restapi.html#delete--connectors-(string-name)-.
        :param connector_name: Configuration parameters for the connector.
        :param dry_run: Whether to log the request instead of sending it.
        :raises ConnectorNotFoundException: Connector not found
        """
        response = await self.request(
            "DELETE", f"/connectors/{connector_name}", dry_run=dry_run
        )
        if response is None:
            return None
        if response.status_code == httpx.codes.NO_CONTENT.value:
            log.info(f"Connector {connector_name} deleted.")
            return None
        if response.status_code == httpx.codes.NOT_FOUND.value:
            raise ConnectorNotFoundException
        if response.status_code == httpx.codes.CONFLICT.value:
            log.warning(
                "Rebalancing in progress while deleting a connector... Retrying..."
            )
            await asyncio.sleep(1)
            return await self.delete_connector(connector_name, dry_run=dry_run)
        raise KafkaConnectError(response)

    async def reset_offset(self, connector_name: str, *, dry_run: bool = False) -> None:
        """Reset the offsets for a connector; the connector must exist, and must be in the STOPPED state.

        API Reference:
            https://docs.confluent.io/platform/current/connect/references/restapi.html#delete--connectors-connector-offsets
        :param connector_name: Configuration parameters for the connector.
        :param dry_run: Whether to log the request instead of sending it.
        :raises ConnectorNotFoundException: Connector not found
        """
        response = await self.request(
            "DELETE", f"/connectors/{connector_name}/offsets", dry_run=dry_run
        )
        if response is None:
            return
        if response.status_code == httpx.codes.OK.value:
            log.info(f"Connector {connector_name} offsets reset.")
            return
        if response.status_code == httpx.codes.NOT_FOUND.value:
            raise ConnectorNotFoundException
        raise KafkaConnectError(response)
