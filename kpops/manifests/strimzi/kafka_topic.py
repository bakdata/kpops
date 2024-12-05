from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ConfigDict, Field, model_validator
from typing_extensions import Any

from kpops.components.common.topic import KafkaTopic
from kpops.manifests.kubernetes import KubernetesManifest, ObjectMeta
from kpops.utils.pydantic import CamelCaseConfigModel

if TYPE_CHECKING:
    try:
        from typing import Self  # pyright: ignore[reportAttributeAccessIssue]
    except ImportError:
        from typing_extensions import Self


# Define the Pydantic model for the spec and metadata
class TopicSpec(CamelCaseConfigModel):
    """Specification of a Kafka topic.

    :param partitions: The number of partitions the topic should have. This cannot be decreased after topic creation. It can be increased after topic creation, but it is important to understand the consequences that has, especially for topics with semantic partitioning. When absent this will default to the broker configuration for `num.partitions`.
    :param replicas: The number of replicas the topic should have. When absent this will default to the broker configuration for `default.replication.factor`.
    :param config: The topic configuration.

    """

    partitions: int = Field(default=1, ge=1)
    replicas: int = Field(default=1, ge=1, le=32767)
    config: dict[str, str | int] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def set_defaults_if_none(cls, values: Any) -> Any:
        if values.get("partitions") is None:
            values["partitions"] = 1
        if values.get("replicas") is None:
            values["replicas"] = 1
        return values


class StrimziKafkaTopic(KubernetesManifest):
    """Represents a Strimzi Kafka Topic CRD.

    CRD definition: https://github.com/strimzi/strimzi-kafka-operator/blob/main/install/cluster-operator/043-Crd-kafkatopic.yaml
    example: https://github.com/strimzi/strimzi-kafka-operator/blob/main/examples/topic/kafka-topic.yaml
    """

    api_version: str = "kafka.strimzi.io/v1beta2"
    kind: str = "KafkaTopic"
    metadata: ObjectMeta
    spec: TopicSpec
    status: dict[str, Any] | None = None

    @classmethod
    def create_strimzi_topic(cls, topic: KafkaTopic, bootstrap_servers: str) -> Self:
        metadata = ObjectMeta.model_validate(
            {
                "name": topic.name,
                "labels": {
                    "strimzi.io/cluster": bootstrap_servers,
                },
            }
        )
        spec = TopicSpec.model_validate(
            {
                "partitions": topic.config.partitions_count,
                "replicas": topic.config.replication_factor,
                "config": topic.config.configs,
            }
        )
        return cls(
            metadata=metadata,
            spec=spec,
        )
