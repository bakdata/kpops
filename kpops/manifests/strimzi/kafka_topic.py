from __future__ import annotations

from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field, model_validator

from kpops.components.common.topic import KafkaTopic
from kpops.config import get_config
from kpops.core.exception import ValidationError
from kpops.manifests.kubernetes import KubernetesManifest, ObjectMeta
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfigModel


class TopicSpec(CamelCaseConfigModel):
    """Specification of a Kafka topic.

    :param partitions: The number of partitions the topic should have. This cannot be decreased after topic creation. It can be increased after topic creation, but it is important to understand the consequences that has, especially for topics with semantic partitioning. When absent this will default to the broker configuration for `num.partitions`.
    :param replicas: The number of replicas the topic should have. When absent this will default to the broker configuration for `default.replication.factor`.
    :param config: The topic configuration. Topic config reference: https://docs.confluent.io/platform/current/installation/configuration/topic-configs.html

    """

    partitions: int = Field(
        default=1, ge=1, description=describe_attr("partitions", __doc__)
    )
    replicas: int = Field(
        default=1, ge=1, le=32767, description=describe_attr("replicas", __doc__)
    )
    config: dict[str, Any] | None = Field(
        default=None, description=describe_attr("config", __doc__)
    )

    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")

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
    def from_topic(cls, topic: KafkaTopic) -> Self:
        strimzi_topic = get_config().strimzi_topic
        if not strimzi_topic:
            msg = "When manifesting KafkaTopic you must define 'strimzi_topic.label' in the config.yaml"
            raise ValidationError(msg)
        cluster_domain, cluster_name = strimzi_topic.cluster_labels

        metadata = ObjectMeta(
            name=topic.name,
            labels={cluster_domain: cluster_name},
        )
        if strimzi_topic.namespace:
            metadata.namespace = strimzi_topic.namespace
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
