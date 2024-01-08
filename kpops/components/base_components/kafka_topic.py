from abc import ABC

from typing_extensions import override

from kpops.components.base_components.models.to_section import TopicConfig
from kpops.components.base_components.pipeline_component import PipelineComponent


class KafkaTopic(PipelineComponent, ABC):
    from_: None
    to: None
    config: TopicConfig

    @override
    def deploy(self, dry_run: bool) -> None:
        self.handlers.topic_handler.create_topic(self, dry_run)
        super().deploy(dry_run)
