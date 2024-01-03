from __future__ import annotations

import logging
from abc import ABC
from functools import cached_property
from typing import NoReturn

from pydantic import Field, PrivateAttr, ValidationInfo, field_validator
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import (
    HelmFlags,
    HelmRepoConfig,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectorConfig,
    KafkaConnectorResetterConfig,
    KafkaConnectorResetterValues,
    KafkaConnectorType,
)
from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
from kpops.components.base_components.models.from_section import FromTopic
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr

log = logging.getLogger("KafkaConnector")


class KafkaConnectorResetter(HelmApp):
    """Helm app for resetting and cleaning a Kafka Connector.

    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to kafka-connect-resetter Helm repo
    :param version: Helm chart version, defaults to "1.0.4"
    """

    app: KafkaConnectorResetterValues
    repo_config: HelmRepoConfig = Field(
        default=HelmRepoConfig(
            repository_name="bakdata-kafka-connect-resetter",
            url="https://bakdata.github.io/kafka-connect-resetter/",
        )
    )
    version: str | None = Field(
        default="1.0.4", description=describe_attr("version", __doc__)
    )

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/kafka-connect-resetter"

    @property
    @override
    def helm_release_name(self) -> str:
        suffix = "-clean"
        return create_helm_release_name(self.full_name + suffix, suffix)

    @property
    @override
    def helm_flags(self) -> HelmFlags:
        return HelmFlags(
            create_namespace=self.config.create_namespace,
            version=self.version,
            wait_for_jobs=True,
            wait=True,
        )

    @override
    def clean(self, dry_run: bool) -> None:
        """Clean the connector from the cluster.

        At first, it deletes the previous cleanup job (connector resetter)
        to make sure that there is no running clean job in the cluster. Then it releases a cleanup job.
        If retain_clean_jobs config is set to false the cleanup job will be deleted subsequently.

        :param dry_run: If the cleanup should be run in dry run mode or not
        """
        log.info(
            magentaify(
                f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {self.full_name}"
            )
        )
        self.destroy(dry_run)

        log.info(
            magentaify(
                f"Connector Cleanup: deploy Connect {self.app.connector_type} resetter for {self.full_name}"
            )
        )
        self.deploy(dry_run)

        if not self.config.retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall Kafka Resetter."))
            self.destroy(dry_run)


class KafkaConnector(PipelineComponent, ABC):
    """Base class for all Kafka connectors.

    Should only be used to set defaults

    :param app: Application-specific settings
    :param namespace: Namespace in which the component shall be deployed
    :param resetter_values: Overriding Kafka Connect Resetter Helm values, e.g. to override the image tag etc.,
        defaults to empty HelmAppValues
    """

    app: KafkaConnectorConfig = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    resetter_values: HelmAppValues = Field(
        default_factory=HelmAppValues,
        description=describe_attr("resetter_values", __doc__),
    )
    _connector_type: KafkaConnectorType = PrivateAttr()

    @cached_property
    def _resetter(self) -> KafkaConnectorResetter:
        return KafkaConnectorResetter(
            config=self.config,
            handlers=self.handlers,
            **self.model_dump(),
            app=KafkaConnectorResetterValues(
                connector_type=self._connector_type.value,
                config=KafkaConnectorResetterConfig(
                    connector=self.full_name,
                    brokers=self.config.kafka_brokers,
                    # **kwargs,  # TODO
                ),
                **self.resetter_values.model_dump(),
            ),
        )

    @field_validator("app", mode="before")
    @classmethod
    def connector_config_should_have_component_name(
        cls,
        app: KafkaConnectorConfig | dict[str, str],
        info: ValidationInfo,
    ) -> KafkaConnectorConfig:
        if isinstance(app, KafkaConnectorConfig):
            app = app.model_dump()
        component_name: str = info.data["prefix"] + info.data["name"]
        connector_name: str | None = app.get("name")
        if connector_name is not None and connector_name != component_name:
            msg = f"Connector name '{connector_name}' should be the same as component name '{component_name}'"
            raise ValueError(msg)
        app["name"] = component_name
        return KafkaConnectorConfig(**app)

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

    _connector_type: KafkaConnectorType = PrivateAttr(KafkaConnectorType.SOURCE)

    @override
    def apply_from_inputs(self, name: str, topic: FromTopic) -> NoReturn:
        msg = "Kafka source connector doesn't support FromSection"
        raise NotImplementedError(msg)

    @override
    def reset(self, dry_run: bool) -> None:
        self._resetter.app.config.offset_topic = self.offset_topic
        self._resetter.reset(dry_run)

    @override
    def clean(self, dry_run: bool) -> None:
        super().clean(dry_run)
        self._resetter.app.config.offset_topic = self.offset_topic
        self._resetter.clean(dry_run)


class KafkaSinkConnector(KafkaConnector):
    """Kafka sink connector model."""

    _connector_type: KafkaConnectorType = PrivateAttr(KafkaConnectorType.SINK)

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
        self._resetter.app.config.delete_consumer_group = False
        self._resetter.reset(dry_run)

    @override
    def clean(self, dry_run: bool) -> None:
        super().clean(dry_run)
        self._resetter.app.config.delete_consumer_group = True
        self._resetter.clean(dry_run)
