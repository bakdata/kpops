from functools import cached_property

from pydantic import Field
from typing_extensions import override

from kpops.components.base_components.kafka_app import (
    KafkaApp,
    KafkaAppCleaner,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap.app_type import AppType
from kpops.components.streams_bootstrap.producer.model import ProducerAppValues
from kpops.utils.docstring import describe_attr


class ProducerAppCleaner(KafkaAppCleaner):
    app: ProducerAppValues

    @property
    @override
    def helm_chart(self) -> str:
        return (
            f"{self.repo_config.repository_name}/{AppType.CLEANUP_PRODUCER_APP.value}"
        )


class ProducerApp(KafkaApp):
    """Producer component.

    This producer holds configuration to use as values for the streams bootstrap
    producer helm chart.

    Note that the producer does not support error topics.

    :param app: Application-specific settings
    :param from_: Producer doesn't support FromSection, defaults to None
    """

    app: ProducerAppValues = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    from_: None = Field(
        default=None,
        alias="from",
        title="From",
        description=describe_attr("from_", __doc__),
    )

    @cached_property
    def _cleaner(self) -> ProducerAppCleaner:
        return ProducerAppCleaner(
            config=self.config,
            handlers=self.handlers,
            **self.model_dump(),
        )

    @override
    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        match topic.type:
            case OutputTopicTypes.ERROR:
                msg = "Producer apps do not support error topics"
                raise ValueError(msg)
            case _:
                super().apply_to_outputs(name, topic)

    @override
    def set_output_topic(self, topic_name: str) -> None:
        self.app.streams.output_topic = topic_name

    @override
    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        self.app.streams.extra_output_topics[role] = topic_name

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.PRODUCER_APP.value}"

    @override
    def clean(self, dry_run: bool) -> None:
        self._cleaner.clean(dry_run)
