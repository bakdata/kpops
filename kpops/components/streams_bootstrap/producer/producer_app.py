# from __future__ import annotations

from pydantic import Field
from typing_extensions import override

from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap.app_type import AppType
from kpops.components.streams_bootstrap.producer.model import ProducerValues
from kpops.utils.docstring import describe_attr


class ProducerApp(KafkaApp):
    """Producer component.

    This producer holds configuration to use as values for the streams bootstrap
    producer helm chart.

    Note that the producer does not support error topics.

    :param app: Application-specific settings
    :param from_: Producer doesn't support FromSection, defaults to None
    """

    app: ProducerValues = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    from_: None = Field(
        default=None,
        alias="from",
        title="From",
        description=describe_attr("from_", __doc__),
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

    @property
    @override
    def clean_up_helm_chart(self) -> str:
        return (
            f"{self.repo_config.repository_name}/{AppType.CLEANUP_PRODUCER_APP.value}"
        )

    @override
    def clean(self, dry_run: bool) -> None:
        self._run_clean_up_job(
            values=self.to_helm_values(),
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
        )
