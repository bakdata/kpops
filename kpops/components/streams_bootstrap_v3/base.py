from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any

import pydantic
from pydantic import AliasChoices, ConfigDict, Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig
from kpops.components.base_components.cleaner import Cleaner
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.config import get_config
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    exclude_by_value,
    exclude_defaults,
)

if TYPE_CHECKING:
    try:
        from typing import Self  # pyright: ignore[reportAttributeAccessIssue]
    except ImportError:
        from typing_extensions import Self


STREAMS_BOOTSTRAP_HELM_REPO = HelmRepoConfig(
    repository_name="bakdata-streams-bootstrap",
    url="https://bakdata.github.io/streams-bootstrap/",
)
STREAMS_BOOTSTRAP_VERSION = "3.0.0"

# Source of the pattern: https://kubernetes.io/docs/concepts/containers/images/#image-names
IMAGE_TAG_PATTERN = r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$"

log = logging.getLogger("StreamsBootstrapV3")


class StreamsBootstrapV3Values(HelmAppValues):
    """Base value class for all streams bootstrap related components.

    :param image_tag: Docker image tag of the streams-bootstrap app.
    """

    image_tag: str = Field(
        default="latest",
        pattern=IMAGE_TAG_PATTERN,
        description=describe_attr("image_tag", __doc__),
    )

    kafka: KafkaConfig = Field(default=..., description=describe_attr("kafka", __doc__))


class StreamsBootstrapV3(HelmApp, ABC):
    """Base for components with a streams-bootstrap Helm chart.

    :param values: streams-bootstrap Helm values
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to streams-bootstrap Helm repo
    :param version: Helm chart version, defaults to "3.0.0"
    """

    values: StreamsBootstrapV3Values = Field(
        default_factory=StreamsBootstrapV3Values,
        description=describe_attr("values", __doc__),
    )

    repo_config: HelmRepoConfig = Field(
        default=STREAMS_BOOTSTRAP_HELM_REPO,
        description=describe_attr("repo_config", __doc__),
    )

    # TODO: validate that version is higher than 3.x.x
    version: str | None = Field(
        default=STREAMS_BOOTSTRAP_VERSION,
        description=describe_attr("version", __doc__),
    )

    @pydantic.model_validator(mode="after")
    def warning_for_latest_image_tag(self) -> Self:
        if self.validate_ and self.values.image_tag == "latest":
            log.warning(
                f"The image tag for component '{self.name}' is set or defaulted to 'latest'. Please, consider providing a stable image tag."
            )
        return self


class KafkaConfig(CamelCaseConfigModel, DescConfigModel):
    """Kafka Streams config.

    :param bootstrap_servers: Brokers
    :param schema_registry_url: URL of the schema registry, defaults to None
    :param labeled_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    bootstrap_servers: str = Field(
        default=..., description=describe_attr("bootstrap_servers", __doc__)
    )
    schema_registry_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "schema_registry_url", "schemaRegistryUrl"
        ),  # TODO: same for other camelcase fields, avoids duplicates during enrichment
        description=describe_attr("schema_registry_url", __doc__),
    )
    labeled_output_topics: dict[str, KafkaTopicStr] = Field(
        default={}, description=describe_attr("labeled_output_topics", __doc__)
    )
    output_topic: KafkaTopicStr | None = Field(
        default=None,
        description=describe_attr("output_topic", __doc__),
        json_schema_extra={},
    )

    model_config = ConfigDict(extra="allow")

    @pydantic.field_validator("labeled_output_topics", mode="before")
    @classmethod
    def deserialize_labeled_output_topics(
        cls, labeled_output_topics: dict[str, str] | Any
    ) -> dict[str, KafkaTopic] | Any:
        if isinstance(labeled_output_topics, dict):
            return {
                label: KafkaTopic(name=topic_name)
                for label, topic_name in labeled_output_topics.items()
            }
        return labeled_output_topics

    @pydantic.field_serializer("labeled_output_topics")
    def serialize_labeled_output_topics(
        self, labeled_output_topics: dict[str, KafkaTopic]
    ) -> dict[str, str]:
        return {label: topic.name for label, topic in labeled_output_topics.items()}

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


class StreamsBootstrapV3Cleaner(Cleaner, StreamsBootstrapV3, ABC):
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
