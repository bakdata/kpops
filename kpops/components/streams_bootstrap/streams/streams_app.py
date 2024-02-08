from functools import cached_property

from pydantic import Field, computed_field
from typing_extensions import override

from kpops.components.base_components.kafka_app import (
    KafkaApp,
    KafkaAppCleaner,
)
from kpops.components.streams_bootstrap import StreamsBootstrap
from kpops.components.streams_bootstrap.app_type import AppType
from kpops.components.streams_bootstrap.streams.model import StreamsAppValues
from kpops.utils.docstring import describe_attr


class StreamsAppCleaner(KafkaAppCleaner):
    app: StreamsAppValues

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.CLEANUP_STREAMS_APP.value}"


class StreamsApp(KafkaApp, StreamsBootstrap):
    """StreamsApp component that configures a streams-bootstrap app.

    :param app: Application-specific settings
    """

    app: StreamsAppValues = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )

    @computed_field
    @cached_property
    def _cleaner(self) -> StreamsAppCleaner:
        return StreamsAppCleaner(
            config=self.config,
            handlers=self.handlers,
            **self.model_dump(by_alias=True, exclude={"_cleaner"}),
        )

    @property
    @override
    def input_topics(self) -> list[str]:
        return self.app.streams.input_topics

    @property
    @override
    def extra_input_topics(self) -> dict[str, list[str]]:
        return self.app.streams.extra_input_topics

    @property
    @override
    def output_topic(self) -> str | None:
        return self.app.streams.output_topic

    @property
    @override
    def extra_output_topics(self) -> dict[str, str]:
        return self.app.streams.extra_output_topics

    @override
    def add_input_topics(self, topics: list[str]) -> None:
        self.app.streams.add_input_topics(topics)

    @override
    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        self.app.streams.add_extra_input_topics(role, topics)

    @override
    def set_input_pattern(self, name: str) -> None:
        self.app.streams.input_pattern = name

    @override
    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        self.app.streams.extra_input_patterns[role] = topic

    @override
    def set_output_topic(self, topic_name: str) -> None:
        self.app.streams.output_topic = topic_name

    @override
    def set_error_topic(self, topic_name: str) -> None:
        self.app.streams.error_topic = topic_name

    @override
    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        self.app.streams.extra_output_topics[role] = topic_name

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.STREAMS_APP.value}"

    @override
    async def reset(self, dry_run: bool) -> None:
        self._cleaner.app.streams.delete_output = False
        await self._cleaner.clean(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        self._cleaner.app.streams.delete_output = True
        await self._cleaner.clean(dry_run)
