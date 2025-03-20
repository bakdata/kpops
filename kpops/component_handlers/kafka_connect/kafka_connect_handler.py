from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self, final

from kpops.component_handlers.kafka_connect.connect_wrapper import ConnectWrapper
from kpops.component_handlers.kafka_connect.exception import (
    ConnectorNotFoundException,
    ConnectorStateException,
)
from kpops.component_handlers.kafka_connect.model import (
    ConnectorCurrentState,
    ConnectorNewState,
)
from kpops.utils.colorify import magentaify
from kpops.utils.dict_differ import render_diff

if TYPE_CHECKING:
    from kpops.component_handlers.kafka_connect.model import KafkaConnectorConfig
    from kpops.config import KpopsConfig

log = logging.getLogger("KafkaConnectHandler")


@final
class KafkaConnectHandler:
    def __init__(self, connect_wrapper: ConnectWrapper):
        self._connect_wrapper = connect_wrapper

    async def create_connector(
        self,
        connector_config: KafkaConnectorConfig,
        *,
        state: ConnectorNewState | None,
        dry_run: bool,
    ) -> None:
        """Create a connector.

        If the connector exists the config and state of that connector gets updated.

        :param connector_config: The connector config.
        :param state: The state that the connector should have afterwards.
        :param dry_run: Whether the connector creation should be run in dry run mode.
        """
        if dry_run:
            await self.__dry_run_connector_creation(connector_config, state)
        else:
            connector_name = connector_config.name
            try:
                await self._connect_wrapper.get_connector(connector_name)
                status = await self._connect_wrapper.get_connector_status(
                    connector_name
                )
                current_state = status.connector.state
                match current_state, state:
                    case ConnectorCurrentState.RUNNING, ConnectorNewState.PAUSED:
                        await self._connect_wrapper.pause_connector(connector_name)
                    case _:
                        pass

                await self._connect_wrapper.update_connector_config(connector_config)

                if (
                    current_state is not ConnectorCurrentState.RUNNING
                    and state is ConnectorNewState.RUNNING
                ):
                    await self._connect_wrapper.resume_connector(connector_name)

            except ConnectorNotFoundException:
                await self._connect_wrapper.create_connector(connector_config, state)

    async def destroy_connector(self, connector_name: str, *, dry_run: bool) -> None:
        """Delete a connector resource from the cluster.

        :param connector_name: The connector name.
        :param dry_run: Whether the connector deletion should be run in dry run mode.
        """
        if dry_run:
            await self.__dry_run_connector_deletion(connector_name)
        else:
            try:
                await self._connect_wrapper.get_connector(connector_name)
                await self._connect_wrapper.delete_connector(connector_name)

            except ConnectorNotFoundException:
                log.warning(
                    f"Connector Destruction: the connector {connector_name} does not exist. Skipping."
                )

    async def __dry_run_connector_creation(
        self,
        connector_config: KafkaConnectorConfig,
        state: ConnectorNewState | None,
    ) -> None:
        connector_name = connector_config.name
        try:
            connector = await self._connect_wrapper.get_connector(connector_name)
            status = await self._connect_wrapper.get_connector_status(connector_name)
            current_state = status.connector.state
            log.info(f"Connector Creation: connector {connector_name} already exists.")

            match current_state, state:
                case ConnectorCurrentState.RUNNING, ConnectorNewState.PAUSED:
                    log.info("Pausing connector")
                case _:
                    pass

            if diff := render_diff(
                connector.config.model_dump(), connector_config.model_dump()
            ):
                log.info(f"Updating config:\n{diff}")

            # TODO: refactor, this should not be here
            log.debug(connector_config.model_dump())
            log.debug(f"PUT /connectors/{connector_name}/config HTTP/1.1")
            log.debug(f"HOST: {self._connect_wrapper.url}")

            if (
                current_state is not ConnectorCurrentState.RUNNING
                and state is ConnectorNewState.RUNNING
            ):
                log.info("Resuming connector")
        except ConnectorNotFoundException:
            diff = render_diff({}, connector_config.model_dump())
            log_msg = [
                f"Connector Creation: connector {connector_name} does not exist. Creating connector"
            ]
            if state:
                log_msg.append(f"in {state.value} state")
            log_msg.append(f"with config:\n{diff}")
            log.info(" ".join(log_msg))
            log.debug("POST /connectors HTTP/1.1")
            log.debug(f"HOST: {self._connect_wrapper.url}")

        errors = await self._connect_wrapper.validate_connector_config(connector_config)
        if len(errors) > 0:
            formatted_errors = "\n".join(errors)
            msg = f"Connector Creation: validating the connector config for connector {connector_name} resulted in the following errors: {formatted_errors}"
            raise ConnectorStateException(msg)
        else:
            log.info(
                f"Connector Creation: connector config for {connector_name} is valid!"
            )

    async def __dry_run_connector_deletion(self, connector_name: str) -> None:
        try:
            await self._connect_wrapper.get_connector(connector_name)
            log.info(
                magentaify(
                    f"Connector Destruction: connector {connector_name} already exists. Deleting connector."
                )
            )
            log.debug(f"DELETE /connectors/{connector_name} HTTP/1.1")
            log.debug(f"HOST: {self._connect_wrapper.url}")
        except ConnectorNotFoundException:
            log.warning(
                f"Connector Destruction: connector {connector_name} does not exist and cannot be deleted. Skipping."
            )

    @classmethod
    def from_kpops_config(cls, config: KpopsConfig) -> Self:
        return cls(
            connect_wrapper=ConnectWrapper(config.kafka_connect),
        )
