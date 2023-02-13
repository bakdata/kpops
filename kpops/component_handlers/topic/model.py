from dataclasses import dataclass
from enum import Enum


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
class TopicConfigResponse:
    data: list[KafkaTopicConfig]

    # TODO: allow extra


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
class KafkaBrokerConfig:
    source: KafkaBrokerConfigSource
    synonyms: list[KafkaBrokerConfigSynonyms]
    value: str | None
    name: str

    # TODO: allow extra


@dataclass(kw_only=True)
class BrokerConfigResponse:
    data: list[KafkaBrokerConfig]

    # TODO: allow extra
