from __future__ import annotations

from typing import TYPE_CHECKING

from kpops.pipeline_deployer.kafka_connect.handler import ConnectorHandler
from kpops.pipeline_deployer.streams_bootstrap.handler import AppHandler

if TYPE_CHECKING:
    from kpops.pipeline_deployer.schema_handler.schema_handler import SchemaHandler
    from kpops.pipeline_deployer.topic.handler import TopicHandler


class PipelineHandlers:
    def __init__(
        self,
        schema_handler: SchemaHandler | None,
        app_handler: AppHandler,
        connector_handler: ConnectorHandler,
        topic_handler: TopicHandler,
    ):
        self.schema_handler = schema_handler
        self.app_handler = app_handler
        self.connector_handler = connector_handler
        self.topic_handler = topic_handler
