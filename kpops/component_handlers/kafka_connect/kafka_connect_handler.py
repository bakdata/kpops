from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from kpops.component_handlers.kafka_connect.connect_wrapper import ConnectWrapper
from kpops.component_handlers.kafka_connect.exception import ConnectorNotFoundException
from kpops.component_handlers.kafka_connect.model import KafkaConnectConfig
from kpops.component_handlers.kafka_connect.timeout import timeout
from kpops.utils.colorify import greenify, magentaify, yellowify
from kpops.utils.dict_differ import render_diff

if TYPE_CHECKING:
    from kpops.cli.pipeline_config import PipelineConfig

log = logging.getLogger("KafkaConnectHandler")


class KafkaConnectHandler:
    def __init__(
        self,
        connect_wrapper: ConnectWrapper,
        timeout: int,
    ):
        self._connect_wrapper = connect_wrapper
        self._timeout = timeout

    def create_connector(
        self,
        connector_name: str,
        kafka_connect_config: KafkaConnectConfig,
        dry_run: bool,
    ) -> None:
        """
        Creates a connector. If the connector exists the config of that connector gets updated.
        :param connector_name: The connector name.
        :param kafka_connect_config: The connector config.
        :param dry_run: If the connector creation should be run in dry run mode.
        """
        if dry_run:
            self.__dry_run_connector_creation(connector_name, kafka_connect_config)
        else:
            try:
                timeout(
                    lambda: self._connect_wrapper.get_connector(connector_name),
                    secs=self._timeout,
                )

                timeout(
                    lambda: self._connect_wrapper.update_connector_config(
                        connector_name, kafka_connect_config
                    ),
                    secs=self._timeout,
                )

            except ConnectorNotFoundException:
                timeout(
                    lambda: self._connect_wrapper.create_connector(
                        connector_name, kafka_connect_config
                    ),
                    secs=self._timeout,
                )

    def destroy_connector(self, connector_name: str, dry_run: bool) -> None:
        """
        Deletes a connector resource from the cluster.
        :param connector_name: The connector name.
        :param dry_run: If the connector deletion should be run in dry run mode.
        """
        if dry_run:
            self.__dry_run_connector_deletion(connector_name)
        else:
            try:
                timeout(
                    lambda: self._connect_wrapper.get_connector(connector_name),
                    secs=self._timeout,
                )

                timeout(
                    lambda: self._connect_wrapper.delete_connector(connector_name),
                    secs=self._timeout,
                )
            except ConnectorNotFoundException:
                log.warning(
                    f"Connector Destruction: the connector {connector_name} does not exist. Skipping."
                )

    def __dry_run_connector_creation(
        self, connector_name: str, kafka_connect_config: KafkaConnectConfig
    ) -> None:
        try:
            connector_config = self._connect_wrapper.get_connector(connector_name)

            log.info(
                yellowify(
                    f"Connector Creation: connector {connector_name} already exists."
                )
            )
            if diff := render_diff(
                connector_config.config, kafka_connect_config.dict()
            ):
                log.info(f"Updating config:\n {diff}")

            log.debug(kafka_connect_config.dict(exclude_unset=True, exclude_none=True))
            log.debug(f"PUT /connectors/{connector_name}/config HTTP/1.1")
            log.debug(f"HOST: {self._connect_wrapper.host}")
        except ConnectorNotFoundException:
            log.info(
                greenify(
                    f"Connector Creation: connector {connector_name} does not exist. Creating connector with config:\n {kafka_connect_config}"
                )
            )
            log.debug("POST /connectors HTTP/1.1")
            log.debug(f"HOST: {self._connect_wrapper.host}")

        errors = self._connect_wrapper.validate_connector_config(kafka_connect_config)
        if len(errors) > 0:
            log.error(
                f"Connector Creation: validating the connector config for connector {connector_name} resulted in the following errors:"
            )
            log.error("\n".join(errors))
            sys.exit(1)
        else:
            log.info(
                greenify(
                    f"Connector Creation: connector config for {connector_name} is valid!"
                )
            )

    def __dry_run_connector_deletion(self, connector_name: str) -> None:
        try:
            self._connect_wrapper.get_connector(connector_name)
            log.info(
                magentaify(
                    f"Connector Destruction: connector {connector_name} already exists. Deleting connector."
                )
            )
            log.debug(f"DELETE /connectors/{connector_name} HTTP/1.1")
            log.debug(f"HOST: {self._connect_wrapper.host}")
        except ConnectorNotFoundException:
            log.warning(
                f"Connector Destruction: connector {connector_name} does not exist and cannot be deleted. Skipping."
            )

    @classmethod
    def from_pipeline_config(
        cls, pipeline_config: PipelineConfig
    ) -> KafkaConnectHandler:  # TODO: annotate as typing.Self once mypy supports it
        return cls(
            connect_wrapper=ConnectWrapper(host=pipeline_config.kafka_connect_host),
            timeout=pipeline_config.timeout,
        )
