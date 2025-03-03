from kpops.component_handlers.topic.model import (
    BrokerConfigResponse,
    TopicConfigResponse,
)
from kpops.component_handlers.topic.utils import (
    get_effective_config,
    parse_and_compare_topic_configs,
)
from kpops.utils.dict_differ import render_diff

kafka_rest_proxy_response = {
    "kind": "KafkaTopicConfigList",
    "metadata": {
        "self": "fake/kafka/v3/clusters/cluster-1/topics/topic-1/configs",
        "next": None,
    },
    "data": [
        {
            "kind": "KafkaTopicConfig",
            "metadata": {
                "self": "https://pkc-00000.region.provider.confluent.cloud/kafka/v3/clusters/cluster-1/topics/topic-1/configs/cleanup.policy",
                "resource_name": "crn:///kafka=cluster-1/topic=topic-1/config=cleanup.policy",
            },
            "cluster_id": "cluster-1",
            "topic_name": "topic-1",
            "name": "cleanup.policy",
            "value": "compact",
            "is_default": False,
            "is_read_only": False,
            "is_sensitive": False,
            "source": "DYNAMIC_TOPIC_CONFIG",
            "synonyms": [
                {
                    "name": "cleanup.policy",
                    "value": "compact",
                    "source": "DYNAMIC_TOPIC_CONFIG",
                },
                {
                    "name": "cleanup.policy",
                    "value": "delete",
                    "source": "DEFAULT_CONFIG",
                },
            ],
        },
        {
            "kind": "KafkaTopicConfig",
            "metadata": {
                "self": "https://fake/kafka/v3/clusters/fake/topics/fake/configs/compression.type",
                "resource_name": "crn:///kafka=fake/topic=topic-1/config=compression.type",
            },
            "cluster_id": "cluster-1",
            "topic_name": "topic-1",
            "name": "compression.type",
            "value": "gzip",
            "is_default": False,
            "is_read_only": False,
            "is_sensitive": False,
            "source": "DYNAMIC_TOPIC_CONFIG",
            "synonyms": [
                {
                    "name": "compression.type",
                    "value": "gzip",
                    "source": "DYNAMIC_TOPIC_CONFIG",
                },
                {
                    "name": "compression.type",
                    "value": "producer",
                    "source": "DEFAULT_CONFIG",
                },
            ],
        },
        {
            "cluster_id": "fake",
            "is_default": True,
            "is_read_only": False,
            "is_sensitive": False,
            "kind": "KafkaTopicConfig",
            "metadata": {
                "resource_name": "crn:///kafka=fake/topic=fake/config=flush.messages",
                "self": "fake/v3/clusters/fake/topics/fake/configs/flush.messages",
            },
            "name": "flush.messages",
            "source": "DEFAULT_CONFIG",
            "synonyms": [
                {
                    "name": "log.flush.interval.messages",
                    "source": "DEFAULT_CONFIG",
                    "value": "9223372036854775807",
                }
            ],
            "topic_name": "fake",
            "value": "9223372036854775807",
        },
        {
            "cluster_id": "fake",
            "is_default": True,
            "is_read_only": False,
            "is_sensitive": False,
            "kind": "KafkaTopicConfig",
            "metadata": {
                "resource_name": "crn:///kafka=fake/topic=fake/config=flush.messages",
                "self": "fake/v3/clusters/fake/topics/fake/configs/flush.messages",
            },
            "name": "flush.ms",
            "source": "DEFAULT_CONFIG",
            "synonyms": [
                {
                    "name": "flush.ms",
                    "source": "DEFAULT_CONFIG",
                    "value": "9223372036854775807",
                }
            ],
            "topic_name": "fake",
            "value": "9223372036854775807",
        },
    ],
}


def test_parse_and_compare_topic_configs():
    topic_config_response = TopicConfigResponse.model_validate(
        kafka_rest_proxy_response
    )

    in_cluster, new_config = parse_and_compare_topic_configs(
        topic_config_response,
        {"flush.ms": 1, "flush.messages": 10, "cleanup.policy": "deletes"},
    )
    assert render_diff(in_cluster, new_config) == (
        "\x1b[31m- cleanup.policy: compact\n"
        "\x1b[0m\x1b[33m?                 ^^^^^^\n"
        "\x1b[0m\x1b[32m+ cleanup.policy: deletes\n"
        "\x1b[0m\x1b[33m?                 ^^^^ ++\n"
        "\x1b[0m\x1b[31m- compression.type: gzip (fallback to default producer)\n"
        "\x1b[0m\x1b[32m+ flush.messages: 10 (was default 9223372036854775807)\n"
        "\x1b[0m\x1b[32m+ flush.ms: 1 (was default 9223372036854775807)\n"
        "\x1b[0m"
    )


def test_compare_single_config_correctly():
    topic_config_response = TopicConfigResponse.model_validate(
        kafka_rest_proxy_response
    )

    in_cluster, new_config = parse_and_compare_topic_configs(
        topic_config_response,
        {"cleanup.policy": "compact"},
    )
    assert render_diff(in_cluster, new_config) == (
        "  cleanup.policy: compact\n"
        "\x1b[31m- compression.type: gzip (fallback to default producer)\n"
        "\x1b[0m"
    )


def test_get_effective_config():
    topic_config_response = BrokerConfigResponse.model_validate(
        {
            "kind": "KafkaBrokerConfigList",
            "metadata": {
                "self": "https://pkc-00000.region.provider.confluent.cloud/kafka/v3/clusters/cluster-1/brokers/-/configs",
                "next": "null",
            },
            "data": [
                {
                    "kind": "KafkaBrokerConfig",
                    "metadata": {
                        "self": "https://pkc-00000.region.provider.confluent.cloud/kafka/v3/clusters/cluster-1/brokers/0/configs/default.replication.factor",
                        "resource_name": "crn:///kafka=cluster-1/broker=0/config=default.replication.factor",
                    },
                    "cluster_id": "cluster-1",
                    "broker_id": "0",
                    "name": "default.replication.factor",
                    "value": "10",
                    "is_default": "true",
                    "is_read_only": "false",
                    "is_sensitive": "false",
                    "source": "STATIC_BROKER_CONFIG",
                    "synonyms": [
                        {
                            "name": "default.replication.factor",
                            "value": "10",
                            "source": "STATIC_BROKER_CONFIG",
                        },
                        {
                            "name": "default.replication.factor",
                            "value": "1",
                            "source": "DEFAULT_CONFIG",
                        },
                    ],
                },
                {
                    "kind": "KafkaBrokerConfig",
                    "metadata": {
                        "self": "https://pkc-00000.region.provider.confluent.cloud/kafka/v3/clusters/cluster-1/brokers/0/configs/num.partitions",
                        "resource_name": "crn:///kafka=cluster-1/broker=0/config=num.partitions",
                    },
                    "cluster_id": "cluster-1",
                    "broker_id": "0",
                    "name": "num.partitions",
                    "value": "1",
                    "is_default": "true",
                    "is_read_only": "false",
                    "is_sensitive": "false",
                    "source": "DEFAULT_CONFIG",
                    "synonyms": [
                        {
                            "name": "num.partitions",
                            "value": "1",
                            "source": "DEFAULT_CONFIG",
                        },
                    ],
                },
                {
                    "kind": "KafkaBrokerConfig",
                    "metadata": {
                        "self": "https://pkc-00000.region.provider.confluent.cloud/kafka/v3/clusters/cluster-1/brokers/0/configs/log.flush.interval.ms",
                        "resource_name": "crn:///kafka=cluster-1/broker=0/config=log.flush.interval.ms",
                    },
                    "cluster_id": "cluster-1",
                    "broker_id": "0",
                    "name": "log.flush.interval.ms",
                    "value": None,
                    "is_default": "true",
                    "is_read_only": "false",
                    "is_sensitive": "false",
                    "source": "DEFAULT_CONFIG",
                    "synonyms": [],
                },
                {
                    "kind": "KafkaBrokerConfig",
                    "metadata": {
                        "self": "https://pkc-00000.region.provider.confluent.cloud/kafka/v3/clusters/cluster-1/brokers/0/configs/heap.opts",
                        "resource_name": "crn:///kafka=cluster-1/broker=0/config=heap.opts",
                    },
                    "cluster_id": "cluster-1",
                    "broker_id": "0",
                    "name": "heap.opts",
                    "value": None,
                    "is_default": "false",
                    "is_read_only": "true",
                    "is_sensitive": "true",
                    "source": "STATIC_BROKER_CONFIG",
                    "synonyms": [
                        {
                            "name": "heap.opts",
                            "value": None,
                            "source": "STATIC_BROKER_CONFIG",
                        },
                    ],
                },
            ],
        }
    )

    effective_config = get_effective_config(
        topic_config_response,
    )
    assert effective_config == {
        "default.replication.factor": "10",
        "num.partitions": "1",
    }
