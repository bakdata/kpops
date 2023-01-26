from pydantic import BaseConfig, Extra
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap.app_type import AppType
from kpops.components.streams_bootstrap.producer.model import ProducerValues


class ProducerApp(KafkaApp):
    """
    Producer component

    This producer holds configuration to use as values for the streams bootstrap produce helm chart.
    """

    _type = "producer"
    app: ProducerValues

    class Config(BaseConfig):
        extra = Extra.allow

    @override
    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        match topic.type:
            case OutputTopicTypes.ERROR:
                raise ValueError("Producer apps do not support error topics")
            case _:
                super().apply_to_outputs(name, topic)

    @override
    def set_output_topic(self, topic_name: str) -> None:
        self.app.streams.output_topic = topic_name

    @override
    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        self.app.streams.extra_output_topics[role] = topic_name

    @override
    def get_helm_chart(self) -> str:
        return f"{self.config.streams_bootstrap_helm_config.repository_name}/{AppType.PRODUCER_APP.value}"

    @property
    @override
    def clean_up_helm_chart(self) -> str:
        return f"{self.config.streams_bootstrap_helm_config.repository_name}/{AppType.CLEANUP_PRODUCER_APP.value}"

    @property
    @override
    def helm_repo_config(self) -> HelmRepoConfig | None:
        return self.config.streams_bootstrap_helm_config

    @override
    def clean(self, dry_run: bool) -> None:
        self._run_clean_up_job(
            values=self.to_helm_values(),
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
        )
