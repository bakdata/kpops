from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Any

from kpops.components.common.kubernetes_model import KubernetesManifest, ObjectMeta
from kpops.components.common.topic import KafkaTopic

if TYPE_CHECKING:
    try:
        from typing import Self  # pyright: ignore[reportAttributeAccessIssue]
    except ImportError:
        from typing_extensions import Self


# Define the Pydantic model for the spec and metadata
class TopicSpec(BaseModel):
    partitions: int = Field(default=1)
    replicas: int = Field(default=1)
    config: dict[str, str | int] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def set_defaults_if_none(cls, values: Any) -> Any:
        if values.get("partitions") is None:
            values["partitions"] = 1
        if values.get("replicas") is None:
            values["replicas"] = 1
        return values


class StrimziKafkaTopic(KubernetesManifest):
    api_version: str = "kafka.strimzi.io/v1beta2"
    kind: str = "KafkaTopic"
    metadata: ObjectMeta
    spec: TopicSpec

    @classmethod
    def create_strimzi_topic(cls, topic: KafkaTopic, bootstrap_servers: str) -> Self:
        metadata = {
            "name": topic.name,
            "labels": {
                "strimzi.io/cluster": bootstrap_servers,
            },
            "kirekhar": None,
        }
        spec = {
            "partitions": topic.config.partitions_count,
            "replicas": topic.config.replication_factor,
            "config": topic.config.configs,
        }
        return cls(metadata=ObjectMeta(**metadata), spec=TopicSpec(**spec))
