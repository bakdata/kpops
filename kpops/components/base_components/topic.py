from abc import ABC

from typing_extensions import override

from kpops.components.base_components.models.to_section import KafkaTopic
from kpops.components.base_components.pipeline_component import PipelineComponent


class TopicComponent(PipelineComponent, ABC):
    from_: None
    to: None
    topic: KafkaTopic

    @property
    @override
    def id(self) -> str:
        return f"topic-{self.full_name}"

    @override
    async def deploy(self, dry_run: bool) -> None:
        await self.handlers.topic_handler.create_topic(self.topic, dry_run)
        await super().deploy(dry_run)

    # TODO: ...
