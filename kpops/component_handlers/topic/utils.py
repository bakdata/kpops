from typing import Any

from kpops.component_handlers.topic.model import (
    BrokerConfigResponse,
    KafkaTopicConfigSource,
    TopicConfigResponse,
)


def parse_and_compare_topic_configs(
    topic_config_in_cluster: TopicConfigResponse, topic_config: dict[str, Any]
) -> tuple[dict[str, str], dict[str, Any]]:
    comparable_in_cluster_config_dict, default_configs = parse_rest_proxy_topic_config(
        topic_config_in_cluster
    )

    cluster_defaults_overwrite = set(topic_config.keys()) - set(
        comparable_in_cluster_config_dict.keys()
    )
    config_overwrites = set(comparable_in_cluster_config_dict.keys()) - set(
        topic_config.keys()
    )
    populate_default_configs(
        cluster_defaults_overwrite,
        default_configs,
        topic_config,
        description_text="was default",
    )

    populate_default_configs(
        config_overwrites,
        default_configs,
        comparable_in_cluster_config_dict,
        description_text="fallback to default",
    )

    return comparable_in_cluster_config_dict, topic_config


def populate_default_configs(
    config_overwrites: set[str],
    default_configs: dict[str, str],
    config_to_populate: dict[str, str],
    description_text: str,
):
    for overwrite in config_overwrites:
        default_config_value = default_configs.get(overwrite)
        if default_config_value:
            config_to_populate[overwrite] = (
                str(config_to_populate[overwrite])
                + f" ({description_text} {default_config_value})"
            )


def parse_rest_proxy_topic_config(
    topic_config_in_cluster: TopicConfigResponse,
) -> tuple[dict[str, str], dict[str, str]]:
    comparable_in_cluster_config_dict: dict[str, str] = {}
    default_configs: dict[str, str] = {}
    for config in topic_config_in_cluster.data:
        if config.source == KafkaTopicConfigSource.DYNAMIC_TOPIC_CONFIG:
            comparable_in_cluster_config_dict[config.name] = config.value
        for synonym in config.synonyms:
            if synonym.source == KafkaTopicConfigSource.DEFAULT_CONFIG:
                default_configs[config.name] = synonym.value
                continue  # we only expect one default value here
    return comparable_in_cluster_config_dict, default_configs


def get_effective_config(
    broker_config_in_cluster: BrokerConfigResponse,
) -> dict[str, str]:
    return {
        config.name: config.value
        for config in broker_config_in_cluster.data
        if config.value
    }
