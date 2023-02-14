from __future__ import annotations

from enum import Enum

from attr import define

from kpops.utils.pydantic import FromDictMixin


@define(kw_only=True)
class TopicSpec(FromDictMixin):
    topic_name: str
    partitions_count: int | None
    replication_factor: int | None
    configs: list[dict[str, str]] | None


@define(kw_only=True)
class TopicResponse(FromDictMixin):
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


@define(kw_only=True)
class KafkaTopicConfigSynonyms:
    name: str
    value: str
    source: KafkaTopicConfigSource

    # TODO: allow extra


@define(kw_only=True)
class KafkaTopicConfig:
    source: KafkaTopicConfigSource
    synonyms: list[KafkaTopicConfigSynonyms]
    value: str
    name: str

    # TODO: allow extra


@define(kw_only=True)
class TopicConfigResponse(FromDictMixin):
    data: list[KafkaTopicConfig]


class KafkaBrokerConfigSource(str, Enum):
    STATIC_BROKER_CONFIG = "STATIC_BROKER_CONFIG"
    DYNAMIC_BROKER_CONFIG = "DYNAMIC_BROKER_CONFIG"
    DEFAULT_CONFIG = "DEFAULT_CONFIG"


@define(kw_only=True)
class KafkaBrokerConfigSynonyms:
    name: str
    value: str | None
    source: KafkaBrokerConfigSource


@define(kw_only=True)
class KafkaBrokerConfig:
    source: KafkaBrokerConfigSource
    synonyms: list[KafkaBrokerConfigSynonyms]
    value: str | None
    name: str


@define(kw_only=True)
class BrokerConfigResponse(FromDictMixin):
    data: list[KafkaBrokerConfig]
