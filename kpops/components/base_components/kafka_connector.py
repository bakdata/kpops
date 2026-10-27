from __future__ import annotations

from abc import ABC
from typing import Any, override

import structlog
from pydantic import PrivateAttr, ValidationInfo, field_validator

from kpops.component_handlers import get_handlers
from kpops.component_handlers.kafka_connect.model import (
    ConnectorNewState,
    KafkaConnectorConfig,
    KafkaConnectorType,
)
from kpops.components.base_components.kafka_app import ConsumesTopics, ProducesTopics
from kpops.components.common.topic import KafkaTopic

log = structlog.get_logger("KafkaConnector")


class KafkaConnector(ProducesTopics, ABC):
    """Base class for all Kafka connectors.

    Should only be used to set defaults

    :param config: Connector config
    :param state: Connector state
    """

    config: KafkaConnectorConfig
    state: ConnectorNewState | None = None
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

    @override
    async def deploy(self, dry_run: bool) -> None:
        """Deploy Kafka Connector (Source/Sink). Create output topics and register schemas if configured."""
        await super().deploy(dry_run)
        await get_handlers().connector_handler.create_connector(
            self.config, state=self.state, dry_run=dry_run
        )

    @override
    async def destroy(self, dry_run: bool) -> None:
        """Delete connector."""
        await get_handlers().connector_handler.destroy_connector(
            self.full_name, dry_run=dry_run
        )

    @override
    async def reset(self, dry_run: bool) -> None:
        """Reset connector offsets. Delete connector afterwards."""
        await get_handlers().connector_handler.reset_connector(
            self.config, dry_run=dry_run
        )
        await super().reset(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        """Delete Kafka Connector. If schema handler is enabled, then remove schemas. Delete all the output topics."""
        await self.reset(dry_run)
        if self.to:
            if schema_handler := get_handlers().schema_handler:
                await schema_handler.delete_schemas(to_section=self.to, dry_run=dry_run)
            for topic in self.to.kafka_topics:
                await get_handlers().topic_handler.delete_topic(topic, dry_run=dry_run)


class KafkaSourceConnector(KafkaConnector):
    """Kafka source connector model."""

    _connector_type: KafkaConnectorType = PrivateAttr(KafkaConnectorType.SOURCE)


class KafkaSinkConnector(ConsumesTopics, KafkaConnector):
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
