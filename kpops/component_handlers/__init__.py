from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define

from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)

if TYPE_CHECKING:
    from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
    from kpops.component_handlers.topic.handler import TopicHandler


@define
class ComponentHandlers:
    schema_handler: SchemaHandler | None
    connector_handler: KafkaConnectHandler
    topic_handler: TopicHandler
