from __future__ import annotations

from typing import TYPE_CHECKING

from kpops.component_handlers.kafka_connect.connector_handler import ConnectorHandler

if TYPE_CHECKING:
    from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
    from kpops.component_handlers.topic.handler import TopicHandler


class ComponentHandlers:
    def __init__(
        self,
        schema_handler: SchemaHandler | None,
        connector_handler: ConnectorHandler,
        topic_handler: TopicHandler,
    ) -> None:
        self.schema_handler = schema_handler
        self.connector_handler = connector_handler
        self.topic_handler = topic_handler
