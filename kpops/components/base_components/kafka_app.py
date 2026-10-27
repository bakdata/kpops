from __future__ import annotations

from abc import ABC
from typing import override

import structlog

from kpops.component_handlers import get_handlers
from kpops.components.base_components.pipeline_component import PipelineComponent

log = structlog.get_logger("KafkaApp")


class KafkaApp(PipelineComponent, ABC):
    """Base component for Kafka-based components."""

    @override
    async def deploy(self, dry_run: bool) -> None:
        if self.to:
            for topic in self.to.kafka_topics:
                await get_handlers().topic_handler.create_topic(topic, dry_run=dry_run)

            if schema_handler := get_handlers().schema_handler:
                await schema_handler.submit_schemas(to_section=self.to, dry_run=dry_run)

        await super().deploy(dry_run)
