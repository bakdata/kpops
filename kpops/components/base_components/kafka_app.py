from __future__ import annotations

import logging
from abc import ABC
from typing import Any

import pydantic
from pydantic import AliasChoices, ConfigDict, Field
from typing_extensions import override

from kpops.component_handlers import get_handlers
from kpops.components.base_components.cleaner import Cleaner
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.config import get_config
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    exclude_by_value,
    exclude_defaults,
)

log = logging.getLogger("KafkaApp")


class KafkaStreamsConfig(CamelCaseConfigModel, DescConfigModel):
    """Kafka Streams config.

    :param brokers: Brokers
    :param schema_registry_url: URL of the schema registry, defaults to None
    :param extra_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    brokers: str = Field(default=..., description=describe_attr("brokers", __doc__))
    schema_registry_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "schema_registry_url", "schemaRegistryUrl"
        ),  # TODO: same for other camelcase fields, avoids duplicates during enrichment
        description=describe_attr("schema_registry_url", __doc__),
    )
    extra_output_topics: dict[str, KafkaTopicStr] = Field(
        default={}, description=describe_attr("extra_output_topics", __doc__)
    )
    output_topic: KafkaTopicStr | None = Field(
        default=None,
        description=describe_attr("output_topic", __doc__),
        json_schema_extra={},
    )

    model_config = ConfigDict(extra="allow")

    @pydantic.field_validator("extra_output_topics", mode="before")
    @classmethod
    def deserialize_extra_output_topics(
        cls, extra_output_topics: dict[str, str] | Any
    ) -> dict[str, KafkaTopic] | Any:
        if isinstance(extra_output_topics, dict):
            return {
                role: KafkaTopic(name=topic_name)
                for role, topic_name in extra_output_topics.items()
            }
        return extra_output_topics

    @pydantic.field_serializer("extra_output_topics")
    def serialize_extra_output_topics(
        self, extra_topics: dict[str, KafkaTopic]
    ) -> dict[str, str]:
        return {role: topic.name for role, topic in extra_topics.items()}

    # TODO(Ivan Yordanov): Currently hacky and potentially unsafe. Find cleaner solution
    @pydantic.model_serializer(mode="wrap", when_used="always")
    def serialize_model(
        self,
        default_serialize_handler: pydantic.SerializerFunctionWrapHandler,
        info: pydantic.SerializationInfo,
    ) -> dict[str, Any]:
        return exclude_defaults(
            self, exclude_by_value(default_serialize_handler(self), None)
        )


class KafkaAppCleaner(Cleaner, ABC):
    """Helm app for resetting and cleaning a streams-bootstrap app."""

    from_: None = None
    to: None = None

    @property
    @override
    def helm_chart(self) -> str:
        raise NotImplementedError

    @override
    async def clean(self, dry_run: bool) -> None:
        """Clean an app using a cleanup job.

        :param dry_run: Dry run command
        """
        log.info(f"Uninstall old cleanup job for {self.helm_release_name}")
        await self.destroy(dry_run)

        log.info(f"Init cleanup job for {self.helm_release_name}")
        await self.deploy(dry_run)

        if not get_config().retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {self.helm_release_name}")
            await self.destroy(dry_run)


class KafkaApp(PipelineComponent, ABC):
    """Base component for Kafka-based components.

    Producer or streaming apps should inherit from this class.

    """

    @override
    async def deploy(self, dry_run: bool) -> None:
        if self.to:
            for topic in self.to.kafka_topics:
                await get_handlers().topic_handler.create_topic(topic, dry_run=dry_run)

            if schema_handler := get_handlers().schema_handler:
                await schema_handler.submit_schemas(to_section=self.to, dry_run=dry_run)

        await super().deploy(dry_run)
