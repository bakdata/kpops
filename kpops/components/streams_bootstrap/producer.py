from pydantic import BaseConfig, Extra
from typing_extensions import override

from kpops.component_handlers.streams_bootstrap.handler import ApplicationType
from kpops.components.base_components.kafka_app import (
    KafkaApp,
    KafkaAppConfig,
    KafkaStreamsConfig,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
)


class ProducerStreamsConfig(KafkaStreamsConfig):
    extra_output_topics: dict[str, str] = {}
    output_topic: str | None


class ProducerValues(KafkaAppConfig):
    streams: ProducerStreamsConfig

    class Config(BaseConfig):
        extra = Extra.allow


class ProducerApp(KafkaApp):
    """
    Producer component

    This producer holds configuration to use as values for the streams bootstrap produce helm chart.
    """

    _type = "producer"
    app: ProducerValues

    class Config(BaseConfig):
        extra = Extra.allow

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @override
    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        match (topic.type):
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
            app_type=ApplicationType.PRODUCER_APP,
            dry_run=dry_run,
        )

    def clean(self, delete_outputs: bool, dry_run: bool):
        if delete_outputs:
            # producer clean up job will delete output topics
            self.handlers.app_handler.clean_app(
                release_name=self.helm_release_name,
                namespace=self.app.namespace,
                dry_run=dry_run,
                delete_outputs=delete_outputs,
                app_type=ApplicationType.CLEANUP_PRODUCER_APP,
                values=self.to_helm_values(),
                retain_clean_jobs=self.config.retain_clean_jobs,
            )
            if (
                self.to
                and self.handlers.schema_handler
                and self.config.clean_producer_schemas
            ):
                self.handlers.schema_handler.delete_schemas(self.to, dry_run=dry_run)

    def destroy(self, dry_run: bool, clean: bool, delete_outputs: bool):
        self.handlers.app_handler.uninstall_app(
            release_name=self.helm_release_name,
            namespace=self.app.namespace,
            dry_run=dry_run,
        )
        if clean:
            self.clean(delete_outputs, dry_run)
