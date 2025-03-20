from __future__ import annotations

import logging
from abc import ABC
from functools import cached_property
from typing import Any, Literal, NoReturn, Self

import pydantic
from pydantic import Field, PrivateAttr, ValidationInfo, field_validator
from typing_extensions import override

from kpops.component_handlers import get_handlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
)
from kpops.component_handlers.kafka_connect.model import (
    ConnectorNewState,
    KafkaConnectorConfig,
    KafkaConnectorType,
)
from kpops.components.base_components.cleaner import Cleaner
from kpops.components.base_components.helm_app import HelmAppValues
from kpops.components.base_components.models.from_section import FromTopic
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.common.topic import KafkaTopic
from kpops.config import get_config
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfigModel, SkipGenerate

log = logging.getLogger("KafkaConnector")


class KafkaConnectorResetterConfig(CamelCaseConfigModel):
    brokers: str
    connector: str
    delete_consumer_group: bool | None = None
    offset_topic: str | None = None


class KafkaConnectorResetterValues(HelmAppValues):
    connector_type: Literal["source", "sink"]
    config: KafkaConnectorResetterConfig


class KafkaConnectorResetter(Cleaner, ABC):
    """Helm app for resetting and cleaning a Kafka Connector.

    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to kafka-connect-resetter Helm repo
    :param version: Helm chart version, defaults to "1.0.4"
    """

    from_: None = None  # pyright: ignore[reportIncompatibleVariableOverride]
    to: None = None  # pyright: ignore[reportIncompatibleVariableOverride]
    values: KafkaConnectorResetterValues  # pyright: ignore[reportIncompatibleVariableOverride]
    repo_config: SkipGenerate[HelmRepoConfig] = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
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
                f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {self.values.config.connector}"
            )
        )
        await self.destroy(dry_run)

        log.info(
            magentaify(
                f"Connector Cleanup: deploy Connect {self.values.connector_type} resetter for {self.values.config.connector}"
            )
        )
        await self.deploy(dry_run)

        if not get_config().retain_clean_jobs:
            log.info(magentaify("Connector Cleanup: uninstall Kafka Resetter."))
            await self.destroy(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        await self.reset(dry_run)


class KafkaConnector(PipelineComponent, ABC):
    """Base class for all Kafka connectors.

    Should only be used to set defaults

    :param config: Connector config
    :param state: Connector state
    :param resetter_namespace: Kubernetes namespace in which the Kafka Connect resetter shall be deployed
    :param resetter_values: Overriding Kafka Connect resetter Helm values, e.g. to override the image tag etc.,
        defaults to empty HelmAppValues
    """

    config: KafkaConnectorConfig = Field(
        description=describe_attr("config", __doc__),
    )
    state: ConnectorNewState | None = Field(
        default=None,
        description=describe_attr("state", __doc__),
    )
    resetter_namespace: str | None = Field(
        default=None, description=describe_attr("resetter_namespace", __doc__)
    )
    resetter_values: HelmAppValues = Field(
        default_factory=HelmAppValues,
        description=describe_attr("resetter_values", __doc__),
    )
    _connector_type: KafkaConnectorType = PrivateAttr()

    @field_validator("config", mode="before")
    @classmethod
    def connector_config_should_have_component_name(
        cls,
        config: KafkaConnectorConfig | dict[str, Any],
        info: ValidationInfo,
    ) -> KafkaConnectorConfig:
        if isinstance(config, KafkaConnectorConfig):
            config = config.model_dump()
        component_name: str = info.data["prefix"] + info.data["name"]
        connector_name: str | None = config.get("name")
        if connector_name is not None and connector_name != component_name:
            msg = f"Connector name '{connector_name}' should be the same as component name '{component_name}'"
            raise ValueError(msg)
        config["name"] = component_name
        return KafkaConnectorConfig.model_validate(config)

    @cached_property
    def _resetter(self) -> KafkaConnectorResetter:
        kwargs: dict[str, Any] = {}
        if self.resetter_namespace:
            kwargs["namespace"] = self.resetter_namespace
        return KafkaConnectorResetter(
            **kwargs,
            **self.model_dump(
                by_alias=True,
                exclude={
                    "_resetter",
                    "resetter_values",
                    "resetter_namespace",
                    "values",
                    "config",
                    "from_",
                    "to",
                },
            ),
            values=KafkaConnectorResetterValues(
                connector_type=self._connector_type.value,
                config=KafkaConnectorResetterConfig(
                    connector=self.full_name,
                    brokers=get_config().kafka_brokers,
                ),
                **self.resetter_values.model_dump(),
            ),
        )

    @override
    async def deploy(self, dry_run: bool) -> None:
        """Deploy Kafka Connector (Source/Sink). Create output topics and register schemas if configured."""
        if self.to:
            for topic in self.to.kafka_topics:
                await get_handlers().topic_handler.create_topic(topic, dry_run=dry_run)

            if schema_handler := get_handlers().schema_handler:
                await schema_handler.submit_schemas(to_section=self.to, dry_run=dry_run)

        await get_handlers().connector_handler.create_connector(
            self.config, state=self.state, dry_run=dry_run
        )

    @override
    async def destroy(self, dry_run: bool) -> None:
        """Delete Kafka Connector (Source/Sink) from the Kafka connect cluster."""
        await get_handlers().connector_handler.destroy_connector(
            self.full_name, dry_run=dry_run
        )

    @override
    async def clean(self, dry_run: bool) -> None:
        """Delete Kafka Connector. If schema handler is enabled, then remove schemas. Delete all the output topics."""
        await super().clean(dry_run)
        if self.to:
            if schema_handler := get_handlers().schema_handler:
                await schema_handler.delete_schemas(to_section=self.to, dry_run=dry_run)
            for topic in self.to.kafka_topics:
                await get_handlers().topic_handler.delete_topic(topic, dry_run=dry_run)


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

    @pydantic.model_validator(mode="after")
    def populate_offset_topic(self) -> Self:
        if self.offset_topic:
            self._resetter.values.config.offset_topic = self.offset_topic
        return self

    @override
    def apply_from_inputs(self, name: str, topic: FromTopic) -> NoReturn:
        msg = "Kafka source connector doesn't support FromSection"
        raise NotImplementedError(msg)

    @override
    async def reset(self, dry_run: bool) -> None:
        """Reset state. Keep connector."""
        await super().reset(dry_run)
        await self._resetter.reset(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        """Delete connector and reset state."""
        await super().clean(dry_run)
        await self._resetter.clean(dry_run)


class KafkaSinkConnector(KafkaConnector):
    """Kafka sink connector model."""

    _connector_type: KafkaConnectorType = PrivateAttr(KafkaConnectorType.SINK)

    @property
    @override
    def input_topics(self) -> list[KafkaTopic]:
        return self.config.topics

    @override
    def add_input_topics(self, topics: list[KafkaTopic]) -> None:
        self.config.topics = KafkaTopic.deduplicate(self.config.topics + topics)

    @override
    def set_input_pattern(self, name: str) -> None:
        self.config.topics_regex = name

    @override
    def set_error_topic(self, topic: KafkaTopic) -> None:
        self.config.errors_deadletterqueue_topic_name = topic

    @override
    async def reset(self, dry_run: bool) -> None:
        """Reset state. Keep consumer group and connector."""
        await super().reset(dry_run)
        self._resetter.values.config.delete_consumer_group = False
        await self._resetter.reset(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        """Delete connector and consumer group."""
        await super().clean(dry_run)
        self._resetter.values.config.delete_consumer_group = True
        await self._resetter.clean(dry_run)
