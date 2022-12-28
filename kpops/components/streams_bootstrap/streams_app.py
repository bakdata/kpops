from pydantic import BaseConfig, BaseModel, Extra
from typing_extensions import override

from kpops.component_handlers.streams_bootstrap.handler import ApplicationType
from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.kafka_app import (
    KafkaApp,
    KafkaAppConfig,
    KafkaStreamsConfig,
)


class StreamsConfig(KafkaStreamsConfig):
    """
    Streams Bootstrap streams section
    """

    input_topics: list[str] = []
    input_pattern: str | None = None
    extra_input_topics: dict[str, list[str]] = {}
    extra_input_patterns: dict[str, str] = {}
    extra_output_topics: dict[str, str] = {}
    output_topic: str | None = None
    error_topic: str | None = None
    config: dict[str, str] = {}

    def add_input_topics(self, topics: list[str]) -> None:
        self.input_topics = deduplicate(self.input_topics + topics)

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        self.extra_input_topics[role] = deduplicate(
            self.extra_input_topics.get(role, []) + topics
        )

    def dict(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        **kwargs
    ) -> dict:
        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            # The following lines are required only for the streams configs since we never not want to export defaults here, just fallback to helm default values
            exclude_defaults=True,
            exclude_none=True,
        )


class StreamAutoScaling(BaseModel):
    consumergroup: str
    topics: list[str] = []

    class Config(BaseConfig):
        extra = Extra.allow


class StreamsAppConfig(KafkaAppConfig):
    """
    StreamsBoostrap app configurations.

    The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.
    """

    streams: StreamsConfig
    autoscaling: StreamAutoScaling | None = None

    class Config(BaseConfig):
        extra = Extra.allow


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

    def substitute_autoscaling_topic_names(self):
        if not self.app.autoscaling:
            return
        self.app.autoscaling.topics = [
            self.substitute_component_variables(topic)
            for topic in self.app.autoscaling.topics
        ]
        self.app.autoscaling.consumergroup = self.substitute_component_variables(
            self.app.autoscaling.consumergroup
        )

    def deploy(self, dry_run: bool):
        if self.to:
            self.handlers.topic_handler.create_topics(
                to_section=self.to, dry_run=dry_run
            )

            if self.handlers.schema_handler:
                self.handlers.schema_handler.submit_schemas(
                    to_section=self.to, dry_run=dry_run
                )

        self.handlers.app_handler.install_app(
            release_name=self.helm_release_name,
            namespace=self.app.namespace,
            values=self.to_helm_values(),
            app_type=ApplicationType.STREAMS_APP,
            dry_run=dry_run,
        )

    def clean(self, delete_outputs: bool, dry_run: bool):
        self.handlers.app_handler.clean_app(
            release_name=self.helm_release_name,
            namespace=self.app.namespace,
            values=self.to_helm_values(),
            app_type=ApplicationType.CLEANUP_STREAMS_APP,
            dry_run=dry_run,
            delete_outputs=delete_outputs,
            retain_clean_jobs=self.config.retain_clean_jobs,
        )
        if (
            self.to
            and delete_outputs
            and self.handlers.schema_handler
            and self.config.clean_streams_apps_schemas
        ):
            self.handlers.schema_handler.delete_schemas(
                to_section=self.to, dry_run=dry_run
            )

    def destroy(self, dry_run: bool, clean: bool, delete_outputs: bool):
        self.handlers.app_handler.uninstall_app(
            release_name=self.helm_release_name,
            namespace=self.app.namespace,
            dry_run=dry_run,
        )
        if clean:
            self.clean(delete_outputs, dry_run)
