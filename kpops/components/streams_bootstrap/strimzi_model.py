from __future__ import annotations

from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Any, override

from kpops.components.common.topic import KafkaTopic


# Define the Pydantic model for the spec and metadata
class Spec(BaseModel):
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


class Metadata(BaseModel):
    name: str
    namespace: Optional[str] = None
    labels: dict[str, str]


class StrimziKafkaTopic(BaseModel):
    api_version: str = Field(default="kafka.strimzi.io/v1beta2", alias="apiVersion")
    kind: str = Field(default="KafkaTopic")
    metadata: Metadata
    spec: Spec

    @override
    def model_dump(self, **_: Any) -> dict[str, Any]:
        return super().model_dump(
            by_alias=True, exclude_none=True, exclude_defaults=False
        )

    @classmethod
    def create_strimzi_topic(cls, topic: KafkaTopic, bootstrap_servers: str) -> Self:
        metadata = {
            "name": topic.name,
            "labels": {
                "strimzi.io/cluster": bootstrap_servers,
            },
        }
        spec = {
            "partitions": topic.config.partitions_count,
            "replicas": topic.config.replication_factor,
            "config": topic.config.configs,
        }
        return cls(metadata=Metadata(**metadata), spec=Spec(**spec))
