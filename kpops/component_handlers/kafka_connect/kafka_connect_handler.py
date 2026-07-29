from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Self, final

from kpops.component_handlers.kafka_connect.exception import (
    ConnectorNotFoundException,
    ConnectorStateException,
)
from kpops.component_handlers.kafka_connect.kafka_connect_api import KafkaConnect
from kpops.component_handlers.kafka_connect.model import (
    ConnectorCurrentState,
    ConnectorNewState,
)
from kpops.utils.colorify import magentaify
from kpops.utils.dict_differ import render_diff

if TYPE_CHECKING:
    from kpops.component_handlers.kafka_connect.model import (
        ConnectorResponse,
        KafkaConnectorConfig,
    )
    from kpops.config import KpopsConfig

log = logging.getLogger("KafkaConnectHandler")


@final
class KafkaConnectHandler:
    def __init__(self, connect_wrapper: KafkaConnect) -> None:
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
        connector_name = connector_config.name
        try:
            connector = await self._connect_wrapper.get_connector(connector_name)
            status = await self._connect_wrapper.get_connector_status(connector_name)
            await self.__update_existing_connector(
                connector,
                connector_config,
                status.connector.state,
                state=state,
                dry_run=dry_run,
            )
        except ConnectorNotFoundException:
            await self.__create_new_connector(connector_config, state, dry_run=dry_run)

        if dry_run:
            await self.__ensure_valid_config(connector_config)

    async def __update_existing_connector(
        self,
        connector: ConnectorResponse,
        connector_config: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
        *,
        state: ConnectorNewState | None,
        dry_run: bool,
    ) -> None:
        connector_name = connector_config.name
        if dry_run:
            log.info(f"Connector Creation: connector {connector_name} already exists.")

        match current_state, state:
            case ConnectorCurrentState.RUNNING, ConnectorNewState.PAUSED:
                if dry_run:
                    log.info("Pausing connector")
                await self._connect_wrapper.pause_connector(
                    connector_name, dry_run=dry_run
                )
            case _:
                pass

        if dry_run and (
            diff := render_diff(
                connector.config.model_dump(), connector_config.model_dump()
            )
        ):
            log.info(f"Updating config:\n{diff}")

        await self._connect_wrapper.update_connector_config(
            connector_config, dry_run=dry_run
        )

        if (
            current_state is not ConnectorCurrentState.RUNNING
            and state is ConnectorNewState.RUNNING
        ):
            if dry_run:
                log.info("Resuming connector")
            await self._connect_wrapper.resume_connector(
                connector_name, dry_run=dry_run
            )

    async def __create_new_connector(
        self,
        connector_config: KafkaConnectorConfig,
        state: ConnectorNewState | None,
        *,
        dry_run: bool,
    ) -> None:
        connector_name = connector_config.name
        if dry_run:
            diff = render_diff({}, connector_config.model_dump())
            log_msg = [
                f"Connector Creation: connector {connector_name} does not exist. Creating connector"
            ]
            if state:
                log_msg.append(f"in {state.value} state")
            log_msg.append(f"with config:\n{diff}")
            log.info(" ".join(log_msg))

        await self._connect_wrapper.create_connector(
            connector_config, state, dry_run=dry_run
        )

    async def __ensure_valid_config(
        self, connector_config: KafkaConnectorConfig
    ) -> None:
        connector_name = connector_config.name
        errors = await self._connect_wrapper.validate_connector_config(connector_config)
        if len(errors) > 0:
            formatted_errors = "\n".join(errors)
            msg = f"Connector Creation: validating the connector config for connector {connector_name} resulted in the following errors: {formatted_errors}"
            raise ConnectorStateException(msg)
        log.info(f"Connector Creation: connector config for {connector_name} is valid!")

    async def destroy_connector(self, connector_name: str, *, dry_run: bool) -> None:
        """Delete a connector resource from the cluster.

        :param connector_name: The connector name.
        :param dry_run: Whether the connector deletion should be run in dry run mode.
        """
        try:
            await self._connect_wrapper.get_connector(connector_name)
            if dry_run:
                log.info(
                    magentaify(
                        f"Connector Destruction: connector {connector_name} already exists. Deleting connector."
                    )
                )
            await self._connect_wrapper.delete_connector(
                connector_name, dry_run=dry_run
            )
        except ConnectorNotFoundException:
            if dry_run:
                log.warning(
                    f"Connector Destruction: connector {connector_name} does not exist and cannot be deleted. Skipping."
                )
            else:
                log.warning(
                    f"Connector Destruction: the connector {connector_name} does not exist. Skipping."
                )

    async def reset_connector(
        self, connector_config: KafkaConnectorConfig, *, dry_run: bool
    ) -> None:
        """Reset connector offsets.

        If the connector does not exist, it is created temporarily in a
        paused state so its offsets can be reset, then deleted again afterwards.

        :param connector_config: The connector config.
        :param dry_run: Whether the connector reset should be run in dry run mode.
        """
        connector_name = connector_config.name
        try:
            await self._connect_wrapper.get_connector(connector_name)
            connector_existed = True
        except ConnectorNotFoundException:
            connector_existed = False
            await self.create_connector(
                connector_config, state=ConnectorNewState.PAUSED, dry_run=dry_run
            )

        try:
            if dry_run:
                log.info(
                    magentaify(
                        f"Connector reset: resetting offsets for connector {connector_name}."
                    )
                )
            await self._connect_wrapper.stop_connector(connector_name, dry_run=dry_run)
            await self._connect_wrapper.reset_offset(connector_name, dry_run=dry_run)
        except ConnectorNotFoundException:
            log.warning(
                f"Connector reset: the connector {connector_name} does not exist. Skipping."
            )
            return

        if not connector_existed:
            if dry_run:
                log.info(
                    magentaify(
                        f"Connector reset: deleting temporarily created connector {connector_name}."
                    )
                )
            try:
                await self._connect_wrapper.delete_connector(
                    connector_name, dry_run=dry_run
                )
            except ConnectorNotFoundException:
                log.warning(
                    f"Connector reset: the connector {connector_name} does not exist. Skipping."
                )

    @classmethod
    def from_kpops_config(cls, config: KpopsConfig) -> Self:
        return cls(
            connect_wrapper=KafkaConnect(config.kafka_connect),
        )
