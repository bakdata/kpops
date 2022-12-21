from __future__ import annotations

from typing import TYPE_CHECKING

from kpops.component_handlers.kafka_connect.handler import ConnectorHandler
from kpops.component_handlers.streams_bootstrap.handler import AppHandler

if TYPE_CHECKING:
    from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
    from kpops.component_handlers.topic.handler import TopicHandler


class ComponentHandlers:
    def __init__(
        self,
        schema_handler: SchemaHandler | None,
        app_handler: AppHandler,
        connector_handler: ConnectorHandler,
        topic_handler: TopicHandler,
    ) -> None:
        self.schema_handler = schema_handler
        self.app_handler = app_handler
        self.connector_handler = connector_handler
        self.topic_handler = topic_handler
