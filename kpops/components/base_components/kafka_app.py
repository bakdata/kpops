from __future__ import annotations

import logging
from abc import ABC
from collections.abc import Iterator

from pydantic import ConfigDict, Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import (
    HelmFlags,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.base_components.helm_app import HelmAppValues
from kpops.components.base_components.models.from_section import (
    FromTopic,
    InputTopicTypes,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.streams_bootstrap import StreamsBootstrap
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfigModel, DescConfigModel

log = logging.getLogger("KafkaApp")


class KafkaStreamsConfig(CamelCaseConfigModel, DescConfigModel):
    """Kafka Streams config.

    :param brokers: Brokers
    :param schema_registry_url: URL of the schema registry, defaults to None
    """

    brokers: str = Field(default=..., description=describe_attr("brokers", __doc__))
    schema_registry_url: str | None = Field(
        default=None, description=describe_attr("schema_registry_url", __doc__)
    )

    model_config = ConfigDict(
        extra="allow",
    )


class KafkaAppValues(HelmAppValues):
    """Settings specific to Kafka Apps.

    :param streams: Kafka streams config
    """

    streams: KafkaStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )


class KafkaAppCleaner(StreamsBootstrap):
    """Helm app for resetting and cleaning a streams-bootstrap app."""

    @property
    @override
    def helm_chart(self) -> str:
        raise NotImplementedError

    @property
    @override
    def helm_release_name(self) -> str:
        suffix = "-clean"
        return create_helm_release_name(self.full_name + suffix, suffix)

    @property
    @override
    def helm_flags(self) -> HelmFlags:
        return HelmFlags(
            create_namespace=self.config.create_namespace,
            version=self.version,
            wait=True,
            wait_for_jobs=True,
        )

    @override
    async def clean(self, dry_run: bool) -> None:
        """Clean an app using a cleanup job.

        :param dry_run: Dry run command
        """
        log.info(f"Uninstall old cleanup job for {self.helm_release_name}")
        await self.destroy(dry_run)

        log.info(f"Init cleanup job for {self.helm_release_name}")
        await self.deploy(dry_run)

        if not self.config.retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {self.helm_release_name}")
            await self.destroy(dry_run)


class KafkaApp(PipelineComponent, ABC):
    """Base component for Kafka-based components.

    Producer or streaming apps should inherit from this class.

    :param to: Topic(s) into which the component will write output,
        defaults to None
    :param app: Application-specific settings
    """

    to: ToSection | None = Field(
        default=None,
        description=describe_attr("to", __doc__),
    )
    app: KafkaAppValues = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_input_topics()
        self.set_output_topics()

    @property
    def input_topics(self) -> list[str]:
        """Get all the input topics from config."""
        return []

    @property
    def extra_input_topics(self) -> dict[str, list[str]]:
        """Get extra input topics list from config."""
        return {}

    @property
    def output_topic(self) -> str | None:
        """Get output topic from config."""
        return None

    @property
    def extra_output_topics(self) -> dict[str, str]:
        """Get extra output topics list from config."""
        return {}

    def add_input_topics(self, topics: list[str]) -> None:
        """Add given topics to the list of input topics.

        :param topics: Input topics
        """

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        """Add given extra topics that share a role to the list of extra input topics.

        :param topics: Extra input topics
        :param role: Topic role
        """

    def set_input_pattern(self, name: str) -> None:
        """Set input pattern.

        :param name: Input pattern name
        """

    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        """Add an input pattern of type extra.

        :param role: Custom identifier belonging to one or multiple topics
        :param topic: Topic name
        """

    def set_output_topic(self, topic_name: str) -> None:
        """Set output topic.

        :param topic_name: Output topic name
        """

    def set_error_topic(self, topic_name: str) -> None:
        """Set error topic.

        :param topic_name: Error topic name
        """

    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        """Add an output topic of type extra.

        :param topic_name: Output topic name
        :param role: Role that is unique to the extra output topic
        """

    def set_input_topics(self) -> None:
        """Put values of config.from into the streams config section of streams bootstrap.

        Supports extra_input_topics (topics by role) or input_topics.
        """
        if self.from_:
            for name, topic in self.from_.topics.items():
                self.apply_from_inputs(name, topic)

    @property
    @override
    def inputs(self) -> Iterator[str]:
        yield from self.input_topics
        for role_topics in self.extra_input_topics.values():
            yield from role_topics

    @property
    @override
    def outputs(self) -> Iterator[str]:
        if output_topic := self.output_topic:
            yield output_topic
        yield from self.extra_output_topics.values()

    def apply_from_inputs(self, name: str, topic: FromTopic) -> None:
        """Add a `from` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        match topic.type:
            case None if topic.role:
                self.add_extra_input_topics(topic.role, [name])
            case InputTopicTypes.PATTERN if topic.role:
                self.add_extra_input_pattern(topic.role, name)
            case InputTopicTypes.PATTERN:
                self.set_input_pattern(name)
            case _:
                self.add_input_topics([name])

    def set_output_topics(self) -> None:
        """Put values of config.to into the producer config section of streams bootstrap.

        Supports extra_output_topics (topics by role) or output_topics.
        """
        if self.to:
            for name, topic in self.to.topics.items():
                self.apply_to_outputs(name, topic)

    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        """Add a `to` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        match topic.type:
            case None if topic.role:
                self.add_extra_output_topic(name, topic.role)
            case OutputTopicTypes.ERROR:
                self.set_error_topic(name)
            case _:
                self.set_output_topic(name)

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
            if topic_config.type != OutputTopicTypes.ERROR and not topic_config.role
        ]
        for input_topic in input_topics:
            self.apply_from_inputs(input_topic, from_topic)

    @override
    async def deploy(self, dry_run: bool) -> None:
        if self.to:
            for topic in self.to.kafka_topics:
                await self.handlers.topic_handler.create_topic(topic, dry_run=dry_run)

            if self.handlers.schema_handler:
                await self.handlers.schema_handler.submit_schemas(
                    to_section=self.to, dry_run=dry_run
                )

        await super().deploy(dry_run)
