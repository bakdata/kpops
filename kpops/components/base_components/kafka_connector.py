from __future__ import annotations

import logging
from abc import ABC
from functools import cached_property
from typing import Any, Literal, NoReturn

from pydantic import Field, validator
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.dry_run_handler import DryRunHandler
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmFlags,
    HelmRepoConfig,
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import trim_release_name
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectorConfig,
    KafkaConnectorType,
    KafkaConnectResetterConfig,
    KafkaConnectResetterValues,
)
from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.models.from_section import FromTopic
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr, describe_object
from kpops.utils.pydantic import CamelCaseConfig

log = logging.getLogger("KafkaConnector")


class KafkaConnector(PipelineComponent, ABC):
    """Base class for all Kafka connectors

    Should only be used to set defaults

    :param type: Component type, defaults to "kafka-connector"
    :param schema_type: Used for schema generation, same as :param:`type`,
        defaults to "kafka-connector"
    :param app: Application-specific settings
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component,
        defaults to HelmRepoConfig(repository_name="bakdata-kafka-connect-resetter", url="https://bakdata.github.io/kafka-connect-resetter/")
    :param namespace: Namespace in which the component shall be deployed
    :param version: Helm chart version, defaults to "1.0.4"
    :param resetter_values: Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.,
        defaults to dict
    """

    type: str = Field(
        default="kafka-connector", description=describe_attr("type", __doc__)
    )
    namespace: str = Field(
        default=...,
        description=describe_attr("namespace", __doc__),
    )
    schema_type: Literal["kafka-connector"] = Field(
        default="kafka-connector",
        title="Component type",
        description=describe_object(__doc__),
        exclude=True,
    )
    app: KafkaConnectorConfig = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    repo_config: HelmRepoConfig = Field(
        default=HelmRepoConfig(
            repository_name="bakdata-kafka-connect-resetter",
            url="https://bakdata.github.io/kafka-connect-resetter/",
        ),
        description=describe_attr("repo_config", __doc__),
    )
    version: str | None = Field(
        default="1.0.4", description=describe_attr("version", __doc__)
    )
    resetter_values: dict = Field(
        default_factory=dict,
        description=describe_attr("resetter_values", __doc__),
    )

    class Config(CamelCaseConfig):
        pass

    @validator("app", pre=True)
    def connector_config_should_have_component_name(
        cls,
        app: KafkaConnectorConfig | dict[str, str],
        values: dict[str, Any],
    ) -> dict[str, str]:
        if isinstance(app, KafkaConnectorConfig):
            app = app.dict()
        component_name = values["prefix"] + values["name"]
        connector_name: str | None = app.get("name")
        if connector_name is not None and connector_name != component_name:
            raise ValueError("Connector name should be the same as component name")
        app["name"] = component_name
        return app

    @cached_property
    def helm(self) -> Helm:
        """Helm object that contains component-specific config such as repo"""
        helm_repo_config = self.repo_config
        helm = Helm(self.config.helm_config)
        helm.add_repo(
            helm_repo_config.repository_name,
            helm_repo_config.url,
            helm_repo_config.repo_auth_flags,
        )
        return helm

    def _get_resetter_helm_chart(self) -> str:
        """Get reseter Helm chart

        :return: returns the component resetter's helm chart
        """
        return f"{self.repo_config.repository_name}/kafka-connect-resetter"

    @cached_property
    def dry_run_handler(self) -> DryRunHandler:
        helm_diff = HelmDiff(self.config.helm_diff_config)
        return DryRunHandler(self.helm, helm_diff, self.namespace)

    @property
    def kafka_connect_resetter_chart(self) -> str:
        """Resetter chart for this component"""
        return f"{self.repo_config.repository_name}/kafka-connect-resetter"

    @property
    def helm_flags(self) -> HelmFlags:
        """Return shared flags for Helm commands"""
        return HelmFlags(
            **self.repo_config.repo_auth_flags.dict(),
            version=self.version,
            create_namespace=self.config.create_namespace,
        )

    @property
    def template_flags(self) -> HelmTemplateFlags:
        """Return flags for Helm template command"""
        return HelmTemplateFlags(
            **self.helm_flags.dict(),
            api_version=self.config.helm_config.api_version,
        )

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

        self.handlers.connector_handler.create_connector(self.app, dry_run=dry_run)

    @override
    def destroy(self, dry_run: bool) -> None:
        self.handlers.connector_handler.destroy_connector(self.name, dry_run=dry_run)

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
        """Clean the connector from the cluster

        At first, it deletes the previous cleanup job (connector resetter)
        to make sure that there is no running clean job in the cluster. Then it releases a cleanup job.
        If the retain_clean_jobs flag is set to false the cleanup job will be deleted.

        :param connector_name: Name of the connector
        :param connector_type: Type of the connector (SINK or SOURCE)
        :param dry_run: If the cleanup should be run in dry run mode or not
        :param retain_clean_jobs: If the cleanup job should be kept
        :param kwargs: Other values for the KafkaConnectResetter
        """
        trimmed_name = self._get_kafka_resetter_release_name(connector_name)

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
            trimmed_name, connector_name, connector_type, dry_run, **kwargs
        )

        if dry_run:
            self.dry_run_handler.print_helm_diff(stdout, trimmed_name, log)

        if not retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall Kafka Resetter."))
            self.__uninstall_connect_resetter(trimmed_name, dry_run)

    def _get_kafka_resetter_release_name(self, connector_name: str) -> str:
        """Get connector resetter's release name

        :param connector_name: Name of the connector to be reset
        :return: The name of the resetter to be used
        """
        suffix = "-clean"
        clean_up_release_name = connector_name + suffix
        trimmed_name = trim_release_name(clean_up_release_name, suffix)
        return trimmed_name

    def __install_connect_resetter(
        self,
        release_name: str,
        connector_name: str,
        connector_type: KafkaConnectorType,
        dry_run: bool,
        **kwargs,
    ) -> str:
        """Install connector resetter

        :param release_name: Release name for the resetter
        :param connector_name: Name of the connector-to-be-reset
        :param connector_type: Type of the connector
        :param dry_run: Whether to dry run the command
        :return: The output of `helm upgrade --install`
        """
        return self.helm.upgrade_install(
            release_name=release_name,
            namespace=self.namespace,
            chart=self.kafka_connect_resetter_chart,
            dry_run=dry_run,
            flags=HelmUpgradeInstallFlags(
                create_namespace=self.config.create_namespace,
                version=self.version,
                wait_for_jobs=True,
                wait=True,
            ),
            values=self._get_kafka_connect_resetter_values(
                connector_name,
                connector_type,
                **kwargs,
            ),
        )

    def _get_kafka_connect_resetter_values(
        self,
        connector_name: str,
        connector_type: KafkaConnectorType,
        **kwargs,
    ) -> dict:
        """Get connector resetter helm chart values

        :param connector_name: Name of the connector
        :param connector_type: Type of the connector
        :return: The Helm chart values of the connector resetter
        """
        return {
            **KafkaConnectResetterValues(
                config=KafkaConnectResetterConfig(
                    connector=connector_name,
                    brokers=self.config.brokers,
                    **kwargs,
                ),
                connector_type=connector_type.value,
                name_override=connector_name,
            ).dict(),
            **self.resetter_values,
        }

    def __uninstall_connect_resetter(self, release_name: str, dry_run: bool) -> None:
        """Uninstall connector resetter

        :param release_name: Name of the release to be uninstalled
        :param dry_run: Whether to do a dry run of the command
        """
        self.helm.uninstall(
            namespace=self.namespace,
            release_name=release_name,
            dry_run=dry_run,
        )


class KafkaSourceConnector(KafkaConnector):
    """Kafka source connector model

    :param type: Component type, defaults to "kafka-source-connector"
    :param schema_type: Used for schema generation, same as :param:`type`,
        defaults to "kafka-source-connector"
    :param offset_topic: offset.storage.topic,
        more info: https://kafka.apache.org/documentation/#connect_running,
        defaults to None
    """

    type: str = Field(
        default="kafka-source-connector",
        description=describe_attr("type", __doc__),
    )
    schema_type: Literal["kafka-source-connector"] = Field(
        default="kafka-source-connector",
        title="Component type",
        description=describe_object(__doc__),
        exclude=True,
    )
    offset_topic: str | None = Field(
        default=None,
        description=describe_attr("offset_topic", __doc__),
    )

    @override
    def apply_from_inputs(self, name: str, topic: FromTopic) -> NoReturn:
        raise NotImplementedError("Kafka source connector doesn't support FromSection")

    @override
    def template(self) -> None:
        values = self._get_kafka_connect_resetter_values(
            self.name,
            KafkaConnectorType.SOURCE,
            offset_topic=self.offset_topic,
        )
        stdout = self.helm.template(
            self._get_kafka_resetter_release_name(self.name),
            self._get_resetter_helm_chart(),
            self.namespace,
            values,
            self.template_flags,
        )
        print(stdout)

    @override
    def reset(self, dry_run: bool) -> None:
        self.__run_kafka_connect_resetter(dry_run)

    @override
    def clean(self, dry_run: bool) -> None:
        super().clean(dry_run)
        self.__run_kafka_connect_resetter(dry_run)

    def __run_kafka_connect_resetter(self, dry_run: bool) -> None:
        """Runs the connector resetter

        :param dry_run: Whether to do a dry run of the command
        """
        self._run_connect_resetter(
            connector_name=self.name,
            connector_type=KafkaConnectorType.SOURCE,
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
            offset_topic=self.offset_topic,
        )


class KafkaSinkConnector(KafkaConnector):
    """Kafka sink connector model

    :param type: Component type, defaults to "kafka-sink-connector"
    :param schema_type: Used for schema generation, same as :param:`type`,
        defaults to "kafka-sink-connector"
    """

    type: str = Field(
        default="kafka-sink-connector",
        description=describe_attr("type", __doc__),
    )
    schema_type: Literal["kafka-sink-connector"] = Field(
        default="kafka-sink-connector",
        title="Component type",
        description=describe_object(__doc__),
        exclude=True,
    )

    @override
    def add_input_topics(self, topics: list[str]) -> None:
        existing_topics: str | None = getattr(self.app, "topics", None)
        topics = existing_topics.split(",") + topics if existing_topics else topics
        topics = deduplicate(topics)
        setattr(self.app, "topics", ",".join(topics))

    @override
    def template(self) -> None:
        values = self._get_kafka_connect_resetter_values(
            self.name, KafkaConnectorType.SINK
        )
        stdout = self.helm.template(
            self._get_kafka_resetter_release_name(self.name),
            self._get_resetter_helm_chart(),
            self.namespace,
            values,
            self.template_flags,
        )
        print(stdout)

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
        """Runs the connector resetter

        :param dry_run: Whether to do a dry run of the command
        """
        self._run_connect_resetter(
            connector_name=self.name,
            connector_type=KafkaConnectorType.SINK,
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
            delete_consumer_group=delete_consumer_group,
        )
