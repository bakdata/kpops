from __future__ import annotations

import json
import logging
from abc import ABC
from functools import cached_property
from typing import ClassVar, Literal, NoReturn

from pydantic import Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import trim_release_name
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectConfig,
    KafkaConnectorType,
    KafkaConnectResetterConfig,
    KafkaConnectResetterValues,
)
from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.models.from_section import FromTopic
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.colorify import magentaify
from kpops.utils.pydantic import CamelCaseConfig

log = logging.getLogger("KafkaConnector")


class KafkaConnector(PipelineComponent, ABC):
    type: ClassVar[str] = "kafka-connect"
    app: KafkaConnectConfig

    repo_config: HelmRepoConfig = HelmRepoConfig(
        repository_name="bakdata-kafka-connect-resetter",
        url="https://bakdata.github.io/kafka-connect-resetter/",
    )
    namespace: str
    version: str = "1.0.4"
    resetter_values: dict = Field(
        default_factory=dict,
        description="Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
    )

    class Config(CamelCaseConfig):
        pass

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prepare_connector_config()

    @cached_property
    def helm(self) -> Helm:
        helm_repo_config = self.repo_config
        helm = Helm(self.config.helm_config)
        helm.add_repo(
            helm_repo_config.repository_name,
            helm_repo_config.url,
            helm_repo_config.repo_auth_flags,
        )
        return helm

    @cached_property
    def helm_diff(self) -> HelmDiff:
        return HelmDiff(self.config.helm_diff_config)

    @property
    def kafka_connect_resetter_chart(self) -> str:
        return f"{self.repo_config.repository_name}/kafka-connect-resetter"

    def prepare_connector_config(self) -> None:
        """
        Substitute component related variables in config
        """
        substituted_config = self.substitute_component_variables(
            json.dumps(self.app.dict())
        )
        out: dict = json.loads(substituted_config)
        self.app = KafkaConnectConfig(**out)

    @override
    def deploy(self, dry_run: bool) -> None:
        if self.to:
            self.handlers.topic_handler.create_topics(
                to_section=self.to, dry_run=dry_run
            )

            if self.handlers.schema_handler:
                self.handlers.schema_handler.submit_schemas(
                    to_section=self.to, dry_run=dry_run
                )

        self.handlers.connector_handler.create_connector(
            connector_name=self.name, kafka_connect_config=self.app, dry_run=dry_run
        )

    @override
    def destroy(self, dry_run: bool) -> None:
        self.handlers.connector_handler.destroy_connector(
            connector_name=self.name, dry_run=dry_run
        )

    @override
    def clean(self, dry_run: bool) -> None:
        if self.to:
            if self.handlers.schema_handler:
                self.handlers.schema_handler.delete_schemas(
                    to_section=self.to, dry_run=dry_run
                )
            self.handlers.topic_handler.delete_topics(self.to, dry_run=dry_run)

    def _run_connect_resetter(
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
        self.__uninstall_connect_resetter(trimmed_name, dry_run)

        log.info(
            magentaify(
                f"Connector Cleanup: deploy Connect {connector_type.value} resetter for {connector_name}"
            )
        )

        stdout = self.__install_connect_resetter(
            trimmed_name, connector_name, connector_type, dry_run, kwargs
        )

        if dry_run and self.helm_diff.config.enable:
            current_release = self.helm.get_manifest(trimmed_name, self.namespace)
            new_release = Helm.load_helm_manifest(stdout)
            helm_diff = HelmDiff.get_diff(current_release, new_release)
            self.helm_diff.log_helm_diff(helm_diff, log)

        if not retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall Kafka Resetter."))
            self.__uninstall_connect_resetter(trimmed_name, dry_run)

    def __install_connect_resetter(
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
            chart=self.kafka_connect_resetter_chart,
            dry_run=dry_run,
            flags=HelmUpgradeInstallFlags(
                version=self.version, wait_for_jobs=True, wait=True
            ),
            values={
                **KafkaConnectResetterValues(
                    config=KafkaConnectResetterConfig(
                        connector=connector_name,
                        brokers=self.config.broker,
                        **kwargs,
                    ),
                    connector_type=connector_type.value,
                    name_override=connector_name,
                ).dict(),
                **self.resetter_values,
            },
        )

    def __uninstall_connect_resetter(self, release_name: str, dry_run: bool) -> None:
        self.helm.uninstall(
            namespace=self.namespace,
            release_name=release_name,
            dry_run=dry_run,
        )


class KafkaSourceConnector(KafkaConnector):
    type: ClassVar[str] = "kafka-source-connector"
    schema_type: Literal["kafka-source-connector"] = Field(
        default="kafka-source-connector", exclude=True
    )
    offset_topic: str | None = None

    @override
    def apply_from_inputs(self, name: str, topic: FromTopic) -> NoReturn:
        raise NotImplementedError("Kafka source connector doesn't support FromSection")

    @override
    def reset(self, dry_run: bool) -> None:
        self.__run_kafka_connect_resetter(dry_run)

    @override
    def clean(self, dry_run: bool) -> None:
        super().clean(dry_run)
        self.__run_kafka_connect_resetter(dry_run)

    def __run_kafka_connect_resetter(self, dry_run: bool) -> None:
        self._run_connect_resetter(
            connector_name=self.name,
            connector_type=KafkaConnectorType.SOURCE,
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
            offset_topic=self.offset_topic,
        )


class KafkaSinkConnector(KafkaConnector):
    type: ClassVar[str] = "kafka-sink-connector"
    schema_type: Literal["kafka-sink-connector"] = Field(
        default="kafka-sink-connector", exclude=True
    )

    @override
    def add_input_topics(self, topics: list[str]) -> None:
        existing_topics: str | None = getattr(self.app, "topics", None)
        topics = existing_topics.split(",") + topics if existing_topics else topics
        topics = deduplicate(topics)
        setattr(self.app, "topics", ",".join(topics))

    @override
    def set_input_pattern(self, name: str) -> None:
        setattr(self.app, "topics.regex", name)

    @override
    def set_error_topic(self, topic_name: str) -> None:
        setattr(self.app, "errors.deadletterqueue.topic.name", topic_name)

    @override
    def reset(self, dry_run: bool) -> None:
        self.__run_kafka_connect_resetter(dry_run, delete_consumer_group=False)

    @override
    def clean(self, dry_run: bool) -> None:
        super().clean(dry_run)
        self.__run_kafka_connect_resetter(dry_run, delete_consumer_group=True)

    def __run_kafka_connect_resetter(
        self, dry_run: bool, delete_consumer_group: bool
    ) -> None:
        self._run_connect_resetter(
            connector_name=self.name,
            connector_type=KafkaConnectorType.SINK,
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
            delete_consumer_group=delete_consumer_group,
        )
