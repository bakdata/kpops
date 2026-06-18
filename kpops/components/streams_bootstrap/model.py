from __future__ import annotations

from typing import Annotated, Any, ClassVar

import pydantic
from pydantic import AliasChoices, ConfigDict, Field

from kpops.components.base_components.helm_app import HelmAppValues
from kpops.components.common.kubernetes_model import (
    Affinity,
    ImagePullPolicy,
    ProtocolSchema,
    Resources,
    ServiceType,
    Toleration,
)
from kpops.components.common.topic import KafkaTopic, KafkaTopicStr
from kpops.utils.pydantic import (
    CamelCaseConfigModel,
    DescConfigModel,
    SerializeAsOptional,
    SerializeAsOptionalModel,
)

# Source of the pattern: https://kubernetes.io/docs/concepts/containers/images/#image-names
IMAGE_TAG_PATTERN = r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$"


class PortConfig(CamelCaseConfigModel, DescConfigModel):
    """Base class for the port configuration of the Kafka Streams application.

    :param container_port: Number of the port to expose.
    :param name: Services can reference port by name (optional).
    :param schema: Protocol for port. Must be UDP, TCP, or SCTP.
    :param service_port: Number of the port of the service (optional)
    """

    container_port: int
    name: str | None = None
    schema_: ProtocolSchema = Field(
        default=ProtocolSchema.TCP,
        alias="schema",  # because schema is already a builtin of Pydantic
    )
    service_port: int | None = None


class ServiceConfig(CamelCaseConfigModel, DescConfigModel):
    """Base model for configuring a service for the Kafka Streams application.

    :param enabled: Whether to create a service.
    :param labels: Additional service labels.
    :param type: Service type.
    """

    enabled: bool = False
    labels: dict[str, str] = {}
    type: ServiceType | None = None


class JavaOptions(CamelCaseConfigModel, DescConfigModel):
    """JVM configuration options.

    :param max_RAM_percentage: Sets the maximum amount of memory that the JVM may use for the Java heap before applying ergonomics heuristics as a percentage of the maximum amount determined as described in the -XX:MaxRAM option
    :param others: List of Java VM options passed to the streams app.
    """

    max_RAM_percentage: int | None = None
    others: list[str] = []


class StreamsBootstrapValues(SerializeAsOptionalModel, HelmAppValues):
    """Base value class for all streams bootstrap related components.

    :param image: Docker image of the Kafka producer app.
    :param image_tag: Docker image tag of the streams-bootstrap app.
    :param image_pull_policy: Docker image pull policy.
    :param image_pull_secrets: Secrets to be used for private registries.
    :param kafka: Kafka configuration for the streams-bootstrap app.
    :param resources: See https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
    :param configuration_env_prefix: Prefix for environment variables to use that should be parsed as command line arguments.
    :param command_line: Map of command line arguments passed to the streams app.
    :param env: Custom environment variables.
    :param secrets: Custom secret environment variables. Prefix with configurationEnvPrefix in order to pass secrets to command line or prefix with KAFKA_ to pass secrets to Kafka Streams configuration.
    :param secret_refs: Inject existing secrets as environment variables. Map key is used as environment variable name. Value consists of secret name and key.
    :param secret_files_refs: Mount existing secrets as volumes
    :param files: Map of files to mount for the app. File will be mounted as $value.mountPath/$key. $value.content denotes file content (recommended to be used with --set-file).
    :param pod_annotations: Map of custom annotations to attach to the pod spec.
    :param pod_labels: Map of custom labels to attach to the pod spec.
    :param liveness_probe: See https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.25/#probe-v1-core
    :param readiness_probe: See https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.25/#probe-v1-core
    :param affinity: Map to configure pod affinities https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity.
    :param tolerations: Array containing taint references. When defined, pods can run on nodes, which would otherwise deny scheduling.
    """

    image: str
    image_tag: str | None = Field(
        default=None,
        pattern=IMAGE_TAG_PATTERN,
    )
    image_pull_policy: ImagePullPolicy | None = None
    image_pull_secrets: SerializeAsOptional[list[dict[str, str]]] = []
    kafka: KafkaConfig
    resources: Resources | None = None
    ports: SerializeAsOptional[list[PortConfig]] = []
    service: ServiceConfig | None = None
    configuration_env_prefix: str | None = None
    command_line: SerializeAsOptional[dict[str, str | bool | int | float]] = {}
    env: SerializeAsOptional[dict[str, str]] = {}
    secrets: SerializeAsOptional[dict[str, str]] = {}
    secret_refs: SerializeAsOptional[dict[str, Any]] = {}
    secret_files_refs: SerializeAsOptional[list[dict[str, Any]]] = []
    files: SerializeAsOptional[dict[str, Any]] = {}
    java_options: JavaOptions | None = None
    pod_annotations: SerializeAsOptional[dict[str, str]] = {}
    pod_labels: SerializeAsOptional[dict[str, str]] = {}
    liveness_probe: SerializeAsOptional[dict[str, Any]] = {}
    readiness_probe: SerializeAsOptional[dict[str, Any]] = {}
    affinity: Affinity | None = None
    tolerations: SerializeAsOptional[list[Toleration]] = []

    @pydantic.model_validator(mode="before")
    @classmethod
    def unsupported_attributes(cls, values: Any) -> Any:
        for attr in ("streams",):
            if attr in values:
                msg = f"streams-bootstrap v3 no longer supports '{attr}' attribute."
                raise ValueError(msg)
        return values


def serialize_labeled_output_topics(
    labeled_output_topics: dict[str, KafkaTopic],
) -> dict[str, str]:
    return {label: topic.name for label, topic in labeled_output_topics.items()}


class KafkaConfig(SerializeAsOptionalModel, CamelCaseConfigModel, DescConfigModel):
    """Kafka Streams config.

    :param bootstrap_servers: Brokers
    :param schema_registry_url: URL of the Schema Registry, defaults to None
    :param labeled_output_topics: Extra output topics
    :param output_topic: Output topic, defaults to None
    """

    bootstrap_servers: str = "${config.kafka_brokers}"
    schema_registry_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "schemaRegistryUrl", "schema_registry_url"
        ),  # TODO: same for other camelcase fields, avoids duplicates during enrichment
        title="Schema Registry URL",
    )
    labeled_output_topics: SerializeAsOptional[
        Annotated[
            dict[str, KafkaTopicStr],
            pydantic.PlainSerializer(serialize_labeled_output_topics),
        ]
    ] = {}
    output_topic: KafkaTopicStr | None = None

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

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
