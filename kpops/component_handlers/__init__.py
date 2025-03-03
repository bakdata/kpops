from __future__ import annotations

from typing import TYPE_CHECKING, Any, final

if TYPE_CHECKING:
    from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
        KafkaConnectHandler,
    )
    from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
    from kpops.component_handlers.topic.handler import TopicHandler


@final
class ComponentHandlers:
    _instance: ComponentHandlers | None = None

    def __new__(
        cls,
        schema_handler: SchemaHandler | None,
        connector_handler: KafkaConnectHandler,
        topic_handler: TopicHandler,
        *args: Any,
        **kwargs: Any,
    ) -> ComponentHandlers:
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(
        self,
        schema_handler: SchemaHandler | None,
        connector_handler: KafkaConnectHandler,
        topic_handler: TopicHandler,
    ) -> None:
        self.schema_handler = schema_handler
        self.connector_handler = connector_handler
        self.topic_handler = topic_handler


def get_handlers() -> ComponentHandlers:
    if not ComponentHandlers._instance:  # pyright: ignore[reportPrivateUsage]
        msg = f"{ComponentHandlers.__name__} has not been initialized"
        raise RuntimeError(msg)
    return ComponentHandlers._instance  # pyright: ignore[reportPrivateUsage]
