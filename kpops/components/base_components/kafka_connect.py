import json
import os
from abc import ABC
from typing import NoReturn

from typing_extensions import override

from kpops.cli.pipeline_config import ENV_PREFIX
from kpops.component_handlers.kafka_connect.handler import KafkaConnectorType
from kpops.component_handlers.kafka_connect.model import KafkaConnectConfig
from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.components.base_components.models.from_section import FromTopic
from kpops.components.base_components.pipeline_component import PipelineComponent


class KafkaConnector(PipelineComponent, ABC):
    _type = "kafka-connect"
    app: KafkaConnectConfig

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.prepare_connector_config()

    def prepare_connector_config(self) -> None:
        """
        Substitute component related variables in config
        """
        substituted_config = self.substitute_component_variables(
            json.dumps(self.app.dict())
        )
        out: dict = json.loads(substituted_config)
        self.app = KafkaConnectConfig(**out)

    @override
    def deploy(self, dry_run: bool) -> None:
        if self.to:
            self.handlers.topic_handler.create_topics(
                to_section=self.to, dry_run=dry_run
            )

            if self.handlers.schema_handler:
                self.handlers.schema_handler.submit_schemas(
                    to_section=self.to, dry_run=dry_run
                )

        self.handlers.connector_handler.create_connector(
            connector_name=self.name, kafka_connect_config=self.app, dry_run=dry_run
        )

    @override
    def destroy(
        self, dry_run: bool, clean: bool = False, delete_outputs: bool = False
    ) -> None:
        self.handlers.connector_handler.destroy_connector(
            connector_name=self.name, dry_run=dry_run
        )

        if clean:
            if delete_outputs and self.to:
                if (
                    self.handlers.schema_handler
                    and self.config.clean_kafka_connect_schemas
                ):
                    self.handlers.schema_handler.delete_schemas(
                        to_section=self.to, dry_run=dry_run
                    )
                self.handlers.topic_handler.delete_topics(self.to, dry_run=dry_run)


class KafkaSourceConnector(KafkaConnector):
    _type = "kafka-source-connector"

    @override
    def apply_from_inputs(self, name: str, topic: FromTopic) -> NoReturn:
        raise NotImplementedError("Kafka source connector doesn't support FromSection")

    @override
    def destroy(
        self, dry_run: bool, clean: bool = False, delete_outputs: bool = False
    ) -> None:
        super().destroy(dry_run, clean, delete_outputs)

        if clean:
            self.handlers.connector_handler.clean_connector(
                connector_name=self.name,
                connector_type=KafkaConnectorType.SOURCE,
                dry_run=dry_run,
                retain_clean_jobs=self.config.retain_clean_jobs,
                offset_topic=os.environ[
                    f"{ENV_PREFIX}KAFKA_CONNECT_RESETTER_OFFSET_TOPIC"
                ],
            )


class KafkaSinkConnector(KafkaConnector):
    _type = "kafka-sink-connector"

    @override
    def add_input_topics(self, topics: list[str]) -> None:
        existing_topics: str | None = getattr(self.app, "topics", None)
        topics = existing_topics.split(",") + topics if existing_topics else topics
        topics = deduplicate(topics)
        setattr(self.app, "topics", ",".join(topics))

    @override
    def set_input_pattern(self, name: str) -> None:
        setattr(self.app, "topics.regex", name)

    @override
    def set_error_topic(self, topic_name: str) -> None:
        setattr(self.app, "errors.deadletterqueue.topic.name", topic_name)

    @override
    def destroy(
        self, dry_run: bool, clean: bool = False, delete_outputs: bool = False
    ) -> None:
        super().destroy(dry_run, clean, delete_outputs)

        if clean:
            self.handlers.connector_handler.clean_connector(
                connector_name=self.name,
                connector_type=KafkaConnectorType.SINK,
                dry_run=dry_run,
                retain_clean_jobs=self.config.retain_clean_jobs,
                delete_consumer_group=delete_outputs,
            )
