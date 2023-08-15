from enum import Enum

from pydantic import BaseConfig, BaseModel, Extra


class TopicSpec(BaseModel):
    topic_name: str
    partitions_count: int | None = None
    replication_factor: int | None = None
    configs: list[dict[str, str]] | None = None

    class ModelConfigs(BaseConfig):
        extra = Extra.forbid


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

    class ModelConfigs(BaseConfig):
        extra = Extra.forbid


class KafkaTopicConfigSource(str, Enum):
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

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseConfig):
        extra = Extra.allow


class KafkaTopicConfig(BaseModel):
    source: KafkaTopicConfigSource
    synonyms: list[KafkaTopicConfigSynonyms]
    value: str
    name: str

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseConfig):
        extra = Extra.allow


class TopicConfigResponse(BaseModel):
    data: list[KafkaTopicConfig]

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseConfig):
        extra = Extra.allow


class KafkaBrokerConfigSource(str, Enum):
    STATIC_BROKER_CONFIG = "STATIC_BROKER_CONFIG"
    DYNAMIC_BROKER_CONFIG = "DYNAMIC_BROKER_CONFIG"
    DEFAULT_CONFIG = "DEFAULT_CONFIG"


class KafkaBrokerConfigSynonyms(BaseModel):
    name: str
    value: str | None = None
    source: KafkaBrokerConfigSource

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseConfig):
        extra = Extra.allow


class KafkaBrokerConfig(BaseModel):
    source: KafkaBrokerConfigSource
    synonyms: list[KafkaBrokerConfigSynonyms]
    value: str | None = None
    name: str

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseConfig):
        extra = Extra.allow


class BrokerConfigResponse(BaseModel):
    data: list[KafkaBrokerConfig]

    # TODO[pydantic]: The `Config` class inherits from another class, please create the `model_config` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    class Config(BaseConfig):
        extra = Extra.allow
