from __future__ import annotations

import logging
from abc import ABC
from functools import cached_property
from typing import TYPE_CHECKING, Any, NoReturn

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
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr

if TYPE_CHECKING:
    from kpops.components.base_components.models.from_section import FromTopic

log = logging.getLogger("KafkaConnector")


class KafkaConnector(PipelineComponent, ABC):
    """Base class for all Kafka connectors.

    Should only be used to set defaults

    :param app: Application-specific settings
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component,
        defaults to HelmRepoConfig(repository_name="bakdata-kafka-connect-resetter", url="https://bakdata.github.io/kafka-connect-resetter/")
    :param namespace: Namespace in which the component shall be deployed
    :param version: Helm chart version, defaults to "1.0.4"
    :param resetter_values: Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.,
        defaults to dict
    :param _connector_type: Defines the type of the connector (Source or Sink)
    """

    namespace: str = Field(
        default=...,
        description=describe_attr("namespace", __doc__),
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

    _connector_type: KafkaConnectorType = Field(default=..., hidden_from_schema=True)

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
            msg = f"Connector name '{connector_name}' should be the same as component name '{component_name}'"
            raise ValueError(msg)
        app["name"] = component_name
        return app

    @cached_property
    def helm(self) -> Helm:
        """Helm object that contains component-specific config such as repo."""
        helm_repo_config = self.repo_config
        helm = Helm(self.config.helm_config)
        helm.add_repo(
            helm_repo_config.repository_name,
            helm_repo_config.url,
            helm_repo_config.repo_auth_flags,
        )
        return helm

    @property
    def _resetter_release_name(self) -> str:
        suffix = "-clean"
        clean_up_release_name = self.full_name + suffix
        return trim_release_name(clean_up_release_name, suffix)

    @property
    def _resetter_helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/kafka-connect-resetter"

    @cached_property
    def dry_run_handler(self) -> DryRunHandler:
        helm_diff = HelmDiff(self.config.helm_diff_config)
        return DryRunHandler(self.helm, helm_diff, self.namespace)

    @property
    def helm_flags(self) -> HelmFlags:
        """Return shared flags for Helm commands."""
        return HelmFlags(
            **self.repo_config.repo_auth_flags.dict(),
            version=self.version,
            create_namespace=self.config.create_namespace,
        )

    @property
    def template_flags(self) -> HelmTemplateFlags:
        """Return flags for Helm template command."""
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
        self.handlers.connector_handler.destroy_connector(
            self.full_name, dry_run=dry_run
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
        dry_run: bool,
        retain_clean_jobs: bool,
        **kwargs,
    ) -> None:
        """Clean the connector from the cluster.

        At first, it deletes the previous cleanup job (connector resetter)
        to make sure that there is no running clean job in the cluster. Then it releases a cleanup job.
        If the retain_clean_jobs flag is set to false the cleanup job will be deleted.

        :param dry_run: If the cleanup should be run in dry run mode or not
        :param retain_clean_jobs: If the cleanup job should be kept
        :param kwargs: Other values for the KafkaConnectResetter
        """
        log.info(
            magentaify(
                f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {self.full_name}"
            )
        )
        self.__uninstall_connect_resetter(self._resetter_release_name, dry_run)

        log.info(
            magentaify(
                f"Connector Cleanup: deploy Connect {self._connector_type.value} resetter for {self.full_name}"
            )
        )

        stdout = self.__install_connect_resetter(dry_run, **kwargs)

        if dry_run:
            self.dry_run_handler.print_helm_diff(
                stdout, self._resetter_release_name, log
            )

        if not retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall Kafka Resetter."))
            self.__uninstall_connect_resetter(self._resetter_release_name, dry_run)

    def __install_connect_resetter(
        self,
        dry_run: bool,
        **kwargs,
    ) -> str:
        """Install connector resetter.

        :param dry_run: Whether to dry run the command
        :return: The output of `helm upgrade --install`
        """
        return self.helm.upgrade_install(
            release_name=self._resetter_release_name,
            namespace=self.namespace,
            chart=self._resetter_helm_chart,
            dry_run=dry_run,
            flags=HelmUpgradeInstallFlags(
                create_namespace=self.config.create_namespace,
                version=self.version,
                wait_for_jobs=True,
                wait=True,
            ),
            values=self._get_kafka_connect_resetter_values(
                **kwargs,
            ),
        )

    def _get_kafka_connect_resetter_values(
        self,
        **kwargs,
    ) -> dict:
        """Get connector resetter helm chart values.

        :return: The Helm chart values of the connector resetter
        """
        return {
            **KafkaConnectResetterValues(
                config=KafkaConnectResetterConfig(
                    connector=self.full_name,
                    brokers=self.config.brokers,
                    **kwargs,
                ),
                connector_type=self._connector_type.value,
                name_override=self.full_name,
            ).dict(),
            **self.resetter_values,
        }

    def __uninstall_connect_resetter(self, release_name: str, dry_run: bool) -> None:
        """Uninstall connector resetter.

        :param release_name: Name of the release to be uninstalled
        :param dry_run: Whether to do a dry run of the command
        """
        self.helm.uninstall(
            namespace=self.namespace,
            release_name=release_name,
            dry_run=dry_run,
        )


class KafkaSourceConnector(KafkaConnector):
    """Kafka source connector model.

    :param offset_topic: offset.storage.topic,
        more info: https://kafka.apache.org/documentation/#connect_running,
        defaults to None
    """

    offset_topic: str | None = Field(
        default=None,
        description=describe_attr("offset_topic", __doc__),
    )

    _connector_type = KafkaConnectorType.SOURCE

    @override
    def apply_from_inputs(self, name: str, topic: FromTopic) -> NoReturn:
        msg = "Kafka source connector doesn't support FromSection"
        raise NotImplementedError(msg)

    @override
    def template(self) -> None:
        values = self._get_kafka_connect_resetter_values(
            offset_topic=self.offset_topic,
        )
        stdout = self.helm.template(
            self._resetter_release_name,
            self._resetter_helm_chart,
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
        """Run the connector resetter.

        :param dry_run: Whether to do a dry run of the command
        """
        self._run_connect_resetter(
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
            offset_topic=self.offset_topic,
        )


class KafkaSinkConnector(KafkaConnector):
    """Kafka sink connector model."""

    _connector_type = KafkaConnectorType.SINK

    @override
    def add_input_topics(self, topics: list[str]) -> None:
        existing_topics: str | None = getattr(self.app, "topics", None)
        topics = existing_topics.split(",") + topics if existing_topics else topics
        topics = deduplicate(topics)
        setattr(self.app, "topics", ",".join(topics))

    @override
    def template(self) -> None:
        values = self._get_kafka_connect_resetter_values()
        stdout = self.helm.template(
            self._resetter_release_name,
            self._resetter_helm_chart,
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
        """Run the connector resetter.

        :param dry_run: Whether to do a dry run of the command
        :param delete_consumer_group: Whether the consumer group should be deleted or not
        """
        self._run_connect_resetter(
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
            delete_consumer_group=delete_consumer_group,
        )
