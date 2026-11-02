from __future__ import annotations

from abc import ABC
from collections.abc import Iterator
from typing import ClassVar, override

import structlog
from pydantic import AliasChoices, Field

from kpops.component_handlers import get_handlers
from kpops.components.base_components.models.from_section import (
    FromSection,
    FromTopic,
    InputTopicTypes,
)
from kpops.components.base_components.models.to_section import ToSection
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.common.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)

log = structlog.get_logger("KafkaApp")


class KafkaApp(PipelineComponent, ABC):
    """Base component for Kafka-based components."""


class ConsumesTopics(KafkaApp, ABC):
    """Capability of a Kafka app to read input from topics and components.

    :param from_: Topic(s) and/or components from which the component will read
        input, defaults to None
    """

    _kpops_capability: ClassVar[bool] = True

    from_: FromSection | None = Field(
        default=None,
        serialization_alias="from",
        validation_alias=AliasChoices("from", "from_"),
        title="From",
    )

    @override
    def _apply_topic_sections(self) -> None:
        self.set_input_topics()
        super()._apply_topic_sections()

    @property
    @override
    def inputs(self) -> Iterator[KafkaTopic]:
        yield from self.input_topics
        for labeled_topics in self.extra_input_topics.values():
            yield from labeled_topics

    @property
    def input_topics(self) -> list[KafkaTopic]:
        """Get all the input topics from config."""
        return []

    @property
    def extra_input_topics(self) -> dict[str, list[KafkaTopic]]:
        """Get extra input topics list from config."""
        return {}

    def add_input_topics(self, topics: list[KafkaTopic]) -> None:
        """Add given topics to the list of input topics.

        :param topics: Input topics
        """

    def add_extra_input_topics(self, label: str, topics: list[KafkaTopic]) -> None:
        """Add given extra topics that share a label to the list of extra input topics.

        :param topics: Extra input topics
        :param label: Topic label
        """

    def set_input_pattern(self, name: str) -> None:
        """Set input pattern.

        :param name: Input pattern name
        """

    def add_extra_input_pattern(self, label: str, topic: str) -> None:
        """Add an input pattern of type extra.

        :param label: Custom identifier belonging to one or multiple topics
        :param topic: Topic name
        """

    def set_input_topics(self) -> None:
        """Put values of config.from into the streams config section of streams-bootstrap.

        Supports extra_input_topics (topics by label) or input_topics.
        """
        if self.from_:
            for name, topic in self.from_.topics.items():
                self.apply_from_inputs(name, topic)

    def apply_from_inputs(self, name: str, topic: FromTopic) -> None:
        """Add a `from` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        kafka_topic = KafkaTopic(name=name)
        match topic.type:
            case None if topic.label:
                self.add_extra_input_topics(topic.label, [kafka_topic])
            case InputTopicTypes.PATTERN if topic.label:
                self.add_extra_input_pattern(topic.label, name)
            case InputTopicTypes.PATTERN:
                self.set_input_pattern(name)
            case _:
                self.add_input_topics([kafka_topic])

    def weave_from_topics(
        self,
        to: ToSection | None,
        from_topic: FromTopic | None = None,
    ) -> None:
        """Weave output topics of upstream component or from component into config.

        Override this method to apply custom logic
        """
        if from_topic is None:
            from_topic = FromTopic(type=InputTopicTypes.INPUT)
        if not to:
            return
        input_topics = [
            topic_name
            for topic_name, topic_config in to.topics.items()
            if topic_config.type != OutputTopicTypes.ERROR and not topic_config.label
        ]
        for input_topic in input_topics:
            self.apply_from_inputs(input_topic, from_topic)


class ProducesTopics(KafkaApp, ABC):
    """Capability of a Kafka app to write output to topics.

    :param to: Topic(s) into which the component will write output,
        defaults to None
    """

    _kpops_capability: ClassVar[bool] = True

    to: ToSection | None = None

    @override
    def _apply_topic_sections(self) -> None:
        self.set_output_topics()
        super()._apply_topic_sections()

    @property
    @override
    def outputs(self) -> Iterator[KafkaTopic]:
        if output_topic := self.output_topic:
            yield output_topic
        yield from self.extra_output_topics.values()

    @property
    def output_topic(self) -> KafkaTopic | None:
        """Get output topic from config."""
        return None

    @property
    def extra_output_topics(self) -> dict[str, KafkaTopic]:
        """Get extra output topics list from config."""
        return {}

    def set_output_topic(self, topic: KafkaTopic) -> None:
        """Set output topic.

        :param topic: Output topic
        """

    def set_error_topic(self, topic: KafkaTopic) -> None:
        """Set error topic.

        :param topic: Error topic
        """

    def add_extra_output_topic(self, topic: KafkaTopic, label: str) -> None:
        """Add an output topic of type extra.

        :param topic: Output topic
        :param label: Label that is unique to the extra output topic
        """

    def set_output_topics(self) -> None:
        """Put values of `to` section into the producer config section of streams-bootstrap.

        Supports extra_output_topics (topics by label) or output_topics.
        """
        if self.to:
            for name, topic in self.to.topics.items():
                self.apply_to_outputs(name, topic)

    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        """Add a `to` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        kafka_topic = KafkaTopic(name=name)
        match topic.type:
            case None if topic.label:
                self.add_extra_output_topic(kafka_topic, topic.label)
            case OutputTopicTypes.ERROR:
                self.set_error_topic(kafka_topic)
            case _:
                self.set_output_topic(kafka_topic)

    @override
    async def deploy(self, dry_run: bool) -> None:
        if self.to:
            for topic in self.to.kafka_topics:
                await get_handlers().topic_handler.create_topic(topic, dry_run=dry_run)

            if schema_handler := get_handlers().schema_handler:
                await schema_handler.submit_schemas(to_section=self.to, dry_run=dry_run)

        await super().deploy(dry_run)
