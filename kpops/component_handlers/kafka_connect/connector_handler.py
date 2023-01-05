from __future__ import annotations

import logging
import sys
from functools import cached_property
from typing import TYPE_CHECKING

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import trim_release_name
from kpops.component_handlers.kafka_connect.connect_wrapper import ConnectWrapper
from kpops.component_handlers.kafka_connect.exception import ConnectorNotFoundException
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectConfig,
    KafkaConnectorType,
    KafkaConnectResetterConfig,
    KafkaConnectResetterValues,
)
from kpops.component_handlers.kafka_connect.timeout import timeout
from kpops.utils.colorify import greenify, magentaify, yellowify
from kpops.utils.dict_differ import render_diff

if TYPE_CHECKING:
    from kpops.cli.pipeline_config import KafkaConnectResetterHelmConfig, PipelineConfig

log = logging.getLogger("KafkaConnect")


class ConnectorHandler:
    def __init__(
        self,
        connect_wrapper: ConnectWrapper,
        timeout: int,
        kafka_connect_resetter_helm_config: KafkaConnectResetterHelmConfig,
        broker: str,
        helm_diff: HelmDiff,
        helm_config: HelmConfig = HelmConfig(),
    ):
        self._connect_wrapper = connect_wrapper
        self._timeout = timeout
        self._helm_config = helm_config
        self._helm_repo_config = kafka_connect_resetter_helm_config.helm_config
        self.helm_diff = helm_diff

        helm_repo_config = kafka_connect_resetter_helm_config.helm_config
        self.kafka_connect_resseter_chart = (
            f"{helm_repo_config.repository_name}/kafka-connect-resetter"
        )
        self.chart_version = kafka_connect_resetter_helm_config.version
        self.namespace = (
            kafka_connect_resetter_helm_config.namespace  # namespace where the re-setter jobs should be deployed to
        )
        self.broker = broker
        self.values = kafka_connect_resetter_helm_config.helm_values

    @cached_property
    def helm(self):
        helm = Helm(self._helm_config)
        helm.add_repo(
            self._helm_repo_config.repository_name,
            self._helm_repo_config.url,
            self._helm_repo_config.repo_auth_flags,
        )
        return helm

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
        clean_up_release_name = connector_name + suffix
        trimmed_name = trim_release_name(clean_up_release_name, suffix)

        log.info(
            magentaify(
                f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {connector_name}"
            )
        )
        self.__uninstall_kafka_resetter(trimmed_name, dry_run)

        log.info(
            magentaify(
                f"Connector Cleanup: deploy Connect {connector_type.value} resetter for {connector_name}"
            )
        )

        stdout = self.__install_kafka_resetter(
            trimmed_name, connector_name, connector_type, dry_run, kwargs
        )

        if dry_run and self.helm_diff.config.enable:
            current_release = self.helm.get_manifest(trimmed_name, self.namespace)
            new_release = Helm.load_helm_manifest(stdout)
            helm_diff = HelmDiff.get_diff(current_release, new_release)
            self.helm_diff.log_helm_diff(helm_diff, log)

        if not retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall Kafka Resetter."))
            self.__uninstall_kafka_resetter(trimmed_name, dry_run)

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

    def __install_kafka_resetter(
        self,
        release_name: str,
        connector_name: str,
        connector_type: KafkaConnectorType,
        dry_run: bool,
        kwargs,
    ) -> str:
        return self.helm.upgrade_install(
            release_name=release_name,
            namespace=self.namespace,
            chart=self.kafka_connect_resseter_chart,
            dry_run=dry_run,
            flags=HelmUpgradeInstallFlags(
                version=self.chart_version, wait_for_jobs=True, wait=True
            ),
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

    def __uninstall_kafka_resetter(self, release_name: str, dry_run: bool) -> None:
        self.helm.uninstall(
            namespace=self.namespace,
            release_name=release_name,
            dry_run=dry_run,
        )

    @classmethod
    def from_pipeline_config(
        cls, pipeline_config: PipelineConfig
    ) -> ConnectorHandler:  # TODO: annotate as typing.Self once mypy supports it
        return cls(
            connect_wrapper=ConnectWrapper(host=pipeline_config.kafka_connect_host),
            timeout=pipeline_config.timeout,
            kafka_connect_resetter_helm_config=pipeline_config.kafka_connect_resetter_config,
            helm_config=pipeline_config.helm_config,
            broker=pipeline_config.broker,
            helm_diff=HelmDiff(pipeline_config.helm_diff_config),
        )
