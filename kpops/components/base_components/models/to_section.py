from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict

from kpops.components.base_components.models import ModelName, ModelVersion, TopicName
from kpops.components.common.topic import KafkaTopic, TopicConfig
from kpops.utils.pydantic import DescConfigModel


class ToSection(DescConfigModel):
    """Holds multiple output topics.

    :param topics: Output topics
    :param models: Data models
    """

    topics: dict[TopicName, TopicConfig] = {}
    models: dict[ModelName, ModelVersion] = {}

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    @property
    def kafka_topics(self) -> list[KafkaTopic]:
        return [
            KafkaTopic(name=topic_name, config=topic_config)
            for topic_name, topic_config in self.topics.items()
        ]
