from pydantic import BaseConfig, Extra
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.streams_bootstrap.app_type import AppType
from kpops.components.streams_bootstrap.streams.model import StreamsAppConfig


class StreamsApp(KafkaApp):
    """
    StreamsApp component that configures a streams bootstrap app
    """

    _type = "streams-app"
    app: StreamsAppConfig

    class Config(BaseConfig):
        extra = Extra.allow

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.substitute_autoscaling_topic_names()

    @override
    def add_input_topics(self, topics: list[str]) -> None:
        self.app.streams.add_input_topics(topics)

    @override
    def add_extra_input_topic(self, role: str, topics: list[str]) -> None:
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

    @override
    def get_helm_chart(self) -> str:
        return f"{self.config.streams_bootstrap_helm_config.repository_name}/{AppType.STREAMS_APP.value}"

    @property
    @override
    def helm_repo_config(self) -> HelmRepoConfig | None:
        return self.config.streams_bootstrap_helm_config

    @override
    def get_clean_up_helm_chart(self) -> str:
        return f"{self.config.streams_bootstrap_helm_config.repository_name}/{AppType.CLEANUP_STREAMS_APP.value}"

    def destroy(self, dry_run: bool, clean: bool, delete_outputs: bool) -> None:
        super().destroy(dry_run, clean, delete_outputs)
        if clean:
            self.clean(dry_run, delete_outputs, self.config.clean_streams_apps_schemas)

    def substitute_autoscaling_topic_names(self) -> None:
        if not self.app.autoscaling:
            return
        self.app.autoscaling.topics = [
            self.substitute_component_variables(topic)
            for topic in self.app.autoscaling.topics
        ]
        self.app.autoscaling.consumergroup = self.substitute_component_variables(
            self.app.autoscaling.consumergroup
        )
