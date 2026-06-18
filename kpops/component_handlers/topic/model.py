from enum import StrEnum
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict


class TopicSpec(BaseModel):
    topic_name: str
    partitions_count: int | None = None
    replication_factor: int | None = None
    configs: list[dict[str, Any]] | None = None


class TopicResponse(BaseModel):
    kind: str = "KafkaTopic"
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


class KafkaTopicConfigSource(StrEnum):
    DYNAMIC_TOPIC_CONFIG = "DYNAMIC_TOPIC_CONFIG"
    DEFAULT_CONFIG = "DEFAULT_CONFIG"
    STATIC_BROKER_CONFIG = "STATIC_BROKER_CONFIG"
    DYNAMIC_CLUSTER_LINK_CONFIG = "DYNAMIC_CLUSTER_LINK_CONFIG"
    DYNAMIC_BROKER_LOGGER_CONFIG = "DYNAMIC_BROKER_LOGGER_CONFIG"
    DYNAMIC_BROKER_CONFIG = "DYNAMIC_BROKER_CONFIG"
    DYNAMIC_DEFAULT_BROKER_CONFIG = "DYNAMIC_DEFAULT_BROKER_CONFIG"
    UNKNOWN = "UNKNOWN"


class KafkaTopicConfigSynonyms(BaseModel):
    name: str
    value: str
    source: KafkaTopicConfigSource

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )


class KafkaTopicConfig(BaseModel):
    source: KafkaTopicConfigSource
    synonyms: list[KafkaTopicConfigSynonyms]
    value: str
    name: str

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )


class TopicConfigResponse(BaseModel):
    data: list[KafkaTopicConfig]

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )


class KafkaBrokerConfigSource(StrEnum):
    STATIC_BROKER_CONFIG = "STATIC_BROKER_CONFIG"
    DYNAMIC_BROKER_CONFIG = "DYNAMIC_BROKER_CONFIG"
    DEFAULT_CONFIG = "DEFAULT_CONFIG"


class KafkaBrokerConfigSynonyms(BaseModel):
    name: str
    value: str | None
    source: KafkaBrokerConfigSource

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )


class KafkaBrokerConfig(BaseModel):
    source: KafkaBrokerConfigSource
    synonyms: list[KafkaBrokerConfigSynonyms]
    value: str | None
    name: str

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )


class BrokerConfigResponse(BaseModel):
    data: list[KafkaBrokerConfig]

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )
