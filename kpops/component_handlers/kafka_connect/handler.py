from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

from kpops.component_handlers.kafka_connect.connect_wrapper import ConnectWrapper
from kpops.component_handlers.kafka_connect.exception import ConnectorNotFoundException
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectConfig,
    KafkaConnectorType,
)
from kpops.component_handlers.kafka_connect.timeout import timeout
from kpops.component_handlers.streams_bootstrap.helm_wrapper import (
    HelmCommandConfig,
    HelmWrapper,
)
from kpops.utils.colorify import greenify, magentaify, yellowify
from kpops.utils.dict_differ import render_diff
from kpops.utils.pydantic import CamelCaseConfig

if TYPE_CHECKING:
    from kpops.cli.pipeline_config import PipelineConfig

log = logging.getLogger("KafkaConnect")


class KafkaConnectResetterConfig(BaseModel):
    brokers: str
    connector: str
    delete_consumer_group: bool | None = None
    offset_topic: str | None = None

    class Config(CamelCaseConfig):
        pass


class KafkaConnectResetterValues(BaseModel):
    connector_type: Literal["source", "sink"]
    config: KafkaConnectResetterConfig
    name_override: str

    class Config(CamelCaseConfig):
        pass

    def dict(self, **_):
        return super().dict(by_alias=True, exclude_none=True)


class ConnectorHandlerNotFoundException(Exception):
    def __init__(self, message="ConnectorHandler was not initialized correctly"):
        super().__init__(message)


class ConnectorHandler:
    def __init__(
        self,
        connect_wrapper: ConnectWrapper,
        timeout: int,
        connector_resetter_helm_wrapper: HelmWrapper,
        namespace: str,
        broker: str,
        values: dict,
    ):
        self._connect_wrapper = connect_wrapper
        self._timeout = timeout
        self._helm_wrapper: HelmWrapper = connector_resetter_helm_wrapper
        self._helm_wrapper.helm_repo_add()
        self.namespace = (
            namespace  # namespace where the re-setter jobs should be deployed to
        )
        self.broker = broker
        self.values = values

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

    def clean_connector(
        self,
        connector_name: str,
        connector_type: KafkaConnectorType,
        dry_run: bool,
        retain_clean_jobs: bool,
        **kwargs,
    ) -> None:
        """
        Cleans the connector from the cluster. At first, it deletes the previous cleanup job (connector resetter)
        to make sure that there is no running clean job in the cluster. Then it releases a cleanup job.
        If the retain_clean_jobs flag is set to false the cleanup job will be deleted.
        :param connector_name: Name of the connector
        :param connector_type: Type of the connector (SINK or SOURCE)
        :param dry_run: If the cleanup should be run in dry run mode or not
        :param retain_clean_jobs: If the cleanup job should be kept
        :param kwargs: Other values for the KafkaConnectResetter
        """
        suffix = "-clean"
        release_name = connector_name + suffix

        log.info(
            magentaify(
                f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {connector_name}"
            )
        )
        self.__delete_clean_up_job_release(release_name, suffix, dry_run)

        log.info(
            magentaify(
                f"Connector Cleanup: deploy Connect {connector_type.value} resetter for {connector_name}"
            )
        )
        self._helm_wrapper.helm_upgrade_install(
            release_name=release_name,
            suffix=suffix,
            namespace=self.namespace,
            app="kafka-connect-resetter",
            dry_run=dry_run,
            helm_command_config=HelmCommandConfig(wait_for_jobs=True, wait=True),
            values={
                **KafkaConnectResetterValues(
                    config=KafkaConnectResetterConfig(
                        connector=connector_name,
                        brokers=self.broker,
                        **kwargs,
                    ),
                    connector_type=connector_type.value,
                    name_override=connector_name,
                ).dict(),
                **self.values,
            },
        )

        if not retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall cleanup job"))
            self.__delete_clean_up_job_release(release_name, suffix, dry_run)

    def __delete_clean_up_job_release(
        self, release_name: str, suffix: str, dry_run: bool
    ) -> None:
        self._helm_wrapper.helm_uninstall(
            namespace=self.namespace,
            release_name=release_name,
            suffix=suffix,
            dry_run=dry_run,
        )

    @classmethod
    def from_pipeline_config(
        cls, pipeline_config: PipelineConfig
    ) -> ConnectorHandler:  # TODO: annotate as typing.Self once mypy supports it
        return cls(
            connect_wrapper=ConnectWrapper(host=pipeline_config.kafka_connect_host),
            timeout=pipeline_config.timeout,
            connector_resetter_helm_wrapper=HelmWrapper(
                pipeline_config.kafka_connect_resetter_config.helm_config
            ),
            # TODO: why is this an optional?
            namespace=pipeline_config.kafka_connect_resetter_config.helm_config.namespace,  # type: ignore
            broker=pipeline_config.broker,
            values=pipeline_config.kafka_connect_resetter_config.helm_values,
        )
