from __future__ import annotations

import logging
from abc import ABC
from functools import cached_property
from typing import Any, NoReturn

from pydantic import Field, PrivateAttr, ValidationInfo, computed_field, field_validator
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
)
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectorConfig,
    KafkaConnectorResetterConfig,
    KafkaConnectorResetterValues,
    KafkaConnectorType,
)
from kpops.components.base_components.cleaner import Cleaner
from kpops.components.base_components.helm_app import HelmAppValues
from kpops.components.base_components.models.from_section import FromTopic
from kpops.components.base_components.models.topic import KafkaTopic
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr

log = logging.getLogger("KafkaConnector")


class KafkaConnectorResetter(Cleaner, ABC):
    """Helm app for resetting and cleaning a Kafka Connector.

    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to kafka-connect-resetter Helm repo
    :param version: Helm chart version, defaults to "1.0.4"
    """

    from_: None = None
    to: None = None
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

    @override
    async def reset(self, dry_run: bool) -> None:
        """Reset connector.

        At first, it deletes the previous cleanup job (connector resetter)
        to make sure that there is no running clean job in the cluster. Then it releases a cleanup job.
        If retain_clean_jobs config is set to false the cleanup job will be deleted subsequently.

        :param dry_run: If the cleanup should be run in dry run mode or not
        """
        log.info(
            magentaify(
                f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {self.app.config.connector}"
            )
        )
        await self.destroy(dry_run)

        log.info(
            magentaify(
                f"Connector Cleanup: deploy Connect {self.app.connector_type} resetter for {self.app.config.connector}"
            )
        )
        await self.deploy(dry_run)

        if not self.config.retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall Kafka Resetter."))
            await self.destroy(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        await self.reset(dry_run)


class KafkaConnector(PipelineComponent, ABC):
    """Base class for all Kafka connectors.

    Should only be used to set defaults

    :param app: Application-specific settings
    :param resetter_namespace: Kubernetes namespace in which the Kafka Connect resetter shall be deployed
    :param resetter_values: Overriding Kafka Connect resetter Helm values, e.g. to override the image tag etc.,
        defaults to empty HelmAppValues
    """

    app: KafkaConnectorConfig = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    resetter_namespace: str | None = Field(
        default=None, description=describe_attr("resetter_namespace", __doc__)
    )
    resetter_values: HelmAppValues = Field(
        default_factory=HelmAppValues,
        description=describe_attr("resetter_values", __doc__),
    )
    _connector_type: KafkaConnectorType = PrivateAttr()

    @field_validator("app", mode="before")
    @classmethod
    def connector_config_should_have_component_name(
        cls,
        app: KafkaConnectorConfig | dict[str, Any],
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

    @cached_property
    def _resetter(self) -> KafkaConnectorResetter:
        kwargs: dict[str, Any] = {}
        if self.resetter_namespace:
            kwargs["namespace"] = self.resetter_namespace
        return KafkaConnectorResetter(
            config=self.config,
            handlers=self.handlers,
            **kwargs,
            **self.model_dump(
                by_alias=True,
                exclude={
                    "_resetter",
                    "resetter_values",
                    "resetter_namespace",
                    "app",
                    "from_",
                    "to",
                },
            ),
            app=KafkaConnectorResetterValues(
                connector_type=self._connector_type.value,
                config=KafkaConnectorResetterConfig(
                    connector=self.full_name,
                    brokers=self.config.kafka_brokers,
                ),
                **self.resetter_values.model_dump(),
            ),
        )

    @override
    async def deploy(self, dry_run: bool) -> None:
        if self.to:
            for topic in self.to.kafka_topics:
                await self.handlers.topic_handler.create_topic(topic, dry_run=dry_run)

            if self.handlers.schema_handler:
                await self.handlers.schema_handler.submit_schemas(
                    to_section=self.to, dry_run=dry_run
                )

        await self.handlers.connector_handler.create_connector(
            self.app, dry_run=dry_run
        )

    @override
    async def destroy(self, dry_run: bool) -> None:
        await self.handlers.connector_handler.destroy_connector(
            self.full_name, dry_run=dry_run
        )

    @override
    async def clean(self, dry_run: bool) -> None:
        if self.to:
            if self.handlers.schema_handler:
                await self.handlers.schema_handler.delete_schemas(
                    to_section=self.to, dry_run=dry_run
                )
            for topic in self.to.kafka_topics:
                await self.handlers.topic_handler.delete_topic(topic, dry_run=dry_run)


class KafkaSourceConnector(KafkaConnector):
    """Kafka source connector model.

    :param offset_topic: `offset.storage.topic`,
        more info: https://kafka.apache.org/documentation/#connect_running,
        defaults to None
    """

    offset_topic: str | None = Field(
        default=None,
        description=describe_attr("offset_topic", __doc__),
    )

    _connector_type: KafkaConnectorType = PrivateAttr(KafkaConnectorType.SOURCE)

    @computed_field
    @cached_property
    def _resetter(self) -> KafkaConnectorResetter:
        return super()._resetter

    @override
    def apply_from_inputs(self, name: str, topic: FromTopic) -> NoReturn:
        msg = "Kafka source connector doesn't support FromSection"
        raise NotImplementedError(msg)

    @override
    async def reset(self, dry_run: bool) -> None:
        self._resetter.app.config.offset_topic = self.offset_topic
        await self._resetter.reset(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        await super().clean(dry_run)
        self._resetter.app.config.offset_topic = self.offset_topic
        await self._resetter.clean(dry_run)


class KafkaSinkConnector(KafkaConnector):
    """Kafka sink connector model."""

    _connector_type: KafkaConnectorType = PrivateAttr(KafkaConnectorType.SINK)

    @computed_field
    @cached_property
    def _resetter(self) -> KafkaConnectorResetter:
        return super()._resetter

    @property
    @override
    def input_topics(self) -> list[KafkaTopic]:
        return self.app.topics

    @override
    def add_input_topics(self, topics: list[KafkaTopic]) -> None:
        self.app.topics = KafkaTopic.deduplicate(self.app.topics + topics)

    @override
    def set_input_pattern(self, name: str) -> None:
        self.app.topics_regex = name

    @override
    def set_error_topic(self, topic: KafkaTopic) -> None:
        self.app.errors_deadletterqueue_topic_name = topic

    @override
    async def reset(self, dry_run: bool) -> None:
        self._resetter.app.config.delete_consumer_group = False
        await self._resetter.reset(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        await super().clean(dry_run)
        self._resetter.app.config.delete_consumer_group = True
        await self._resetter.clean(dry_run)
