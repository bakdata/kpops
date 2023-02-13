from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import Enum

from apischema import deserialize
from typing_extensions import Self


# TODO: remove
class AllowExtraMixin:
    def __init__(self, **kwargs) -> None:  # allow extra fields passed as kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


# TODO: remove
# class FromDictMixin:
#     @classmethod
#     def from_dict(cls, d: dict) -> Self:
#         return cls(
#             **{k: v for k, v in d.items() if k in inspect.signature(cls).parameters}
#         )


class FromDictMixin:
    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return deserialize(cls, data, additional_properties=True)


@dataclass(kw_only=True)
class TopicSpec:
    topic_name: str
    partitions_count: int | None
    replication_factor: int | None
    configs: list[dict[str, str]] | None


@dataclass(kw_only=True)
class TopicResponse:
    metadata: dict[str, str]
    cluster_id: str
    topic_name: str
    is_internal: bool
    replication_factor: int
    partitions: dict[str, str]
    configs: dict[str, str]
    partition_reassignments: dict[str, str]
    partitions_count: int = (
        1
        # HACK: workaround for field being absent in Kafka REST response
        # https://github.com/confluentinc/kafka-rest/issues/1085
    )
    kind: str = "KafkaTopic"


class KafkaTopicConfigSource(str, Enum):
    DYNAMIC_TOPIC_CONFIG = "DYNAMIC_TOPIC_CONFIG"
    DEFAULT_CONFIG = "DEFAULT_CONFIG"


@dataclass(kw_only=True)
class KafkaTopicConfigSynonyms:
    name: str
    value: str
    source: KafkaTopicConfigSource

    # TODO: allow extra


@dataclass(kw_only=True)
class KafkaTopicConfig:
    source: KafkaTopicConfigSource
    synonyms: list[KafkaTopicConfigSynonyms]
    value: str
    name: str

    # TODO: allow extra


@dataclass(kw_only=True)
class TopicConfigResponse(FromDictMixin):
    data: list[KafkaTopicConfig]


class KafkaBrokerConfigSource(str, Enum):
    STATIC_BROKER_CONFIG = "STATIC_BROKER_CONFIG"
    DYNAMIC_BROKER_CONFIG = "DYNAMIC_BROKER_CONFIG"
    DEFAULT_CONFIG = "DEFAULT_CONFIG"


@dataclass(kw_only=True)
class KafkaBrokerConfigSynonyms:
    name: str
    value: str | None
    source: KafkaBrokerConfigSource

    # TODO: allow extra


@dataclass(kw_only=True)
class KafkaBrokerConfig(FromDictMixin):
    source: KafkaBrokerConfigSource
    synonyms: list[KafkaBrokerConfigSynonyms]
    value: str | None
    name: str


@dataclass(kw_only=True)
class BrokerConfigResponse(FromDictMixin):
    data: list[KafkaBrokerConfig]
