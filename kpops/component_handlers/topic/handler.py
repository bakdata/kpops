from __future__ import annotations

from typing import Any, final

import structlog

from kpops.component_handlers.topic.exception import (
    TopicNotFoundException,
    TopicTransactionError,
)
from kpops.component_handlers.topic.kafka_rest import KafkaRest
from kpops.component_handlers.topic.model import (
    TopicConfigResponse,
    TopicResponse,
    TopicSpec,
)
from kpops.component_handlers.topic.utils import (
    get_effective_config,
    parse_and_compare_topic_configs,
    parse_rest_proxy_topic_config,
)
from kpops.components.common.topic import KafkaTopic
from kpops.utils.colorify import greenify, magentaify
from kpops.utils.dict_differ import Diff, DiffType, render_diff

log = structlog.get_logger("KafkaTopic")


@final
class TopicHandler:
    def __init__(self, kafka_rest: KafkaRest) -> None:
        self.kafka_rest = kafka_rest

    async def create_topic(self, topic: KafkaTopic, dry_run: bool) -> None:
        """Create a new Kafka topic or update topic configuration if it already exists.

        :param topic: Kafka topic to be created or updated
        :param dry_run: Whether to do a dry run without making changes
        :raises TopicTransactionError: Partition count of topic changed
        :raises TopicTransactionError: Replication factor of topic changed
        """
        topic_spec = self.__prepare_body(topic)
        if dry_run:
            await self.__dry_run_topic_creation(topic, topic_spec)
        else:
            await self.__execute_topic_creation(topic, topic_spec)

    async def delete_topic(self, topic: KafkaTopic, dry_run: bool) -> None:
        """Delete an existing Kafka topic.

        :param topic: Kafka topic to be deleted
        :param dry_run: Whether to do a dry run without making changes
        """
        if dry_run:
            await self.__dry_run_topic_deletion(topic.name)
        else:
            await self.__execute_topic_deletion(topic.name)

    @staticmethod
    def __get_topic_config_diff(
        cluster_config: TopicConfigResponse, current_config: dict[str, Any]
    ) -> list[Diff[str, Any]]:
        comparable_in_cluster_config_dict, _ = parse_rest_proxy_topic_config(
            cluster_config
        )
        return list(Diff.from_dicts(comparable_in_cluster_config_dict, current_config))

    async def __dry_run_topic_creation(
        self, topic: KafkaTopic, topic_spec: TopicSpec
    ) -> None:
        try:
            topic_in_cluster = await self.kafka_rest.get_topic(topic.name)
            topic_name = topic_in_cluster.topic_name
            topic_config_in_cluster = await self.kafka_rest.get_topic_config(topic_name)
            in_cluster_config, new_config = parse_and_compare_topic_configs(
                topic_config_in_cluster, topic.config.configs
            )
            if diff := render_diff(in_cluster_config, new_config):
                log.info("Config changes for topic", topic_name=topic_name, diff=diff)

            log.info("Topic already exists in cluster.", topic_name=topic_name)

            broker_config = await self.kafka_rest.get_broker_config()
            effective_config = get_effective_config(broker_config)

            self.__check_partition_count(topic_in_cluster, topic_spec, effective_config)
            self.__check_replication_factor(
                topic_in_cluster, topic_spec, effective_config
            )
        except TopicNotFoundException:
            log.info(
                greenify(
                    f"Topic Creation: {topic.name} does not exist in the cluster. Creating topic."
                )
            )

    async def __execute_topic_creation(
        self, topic: KafkaTopic, topic_spec: TopicSpec
    ) -> None:
        try:
            await self.kafka_rest.get_topic(topic.name)
            topic_config_in_cluster = await self.kafka_rest.get_topic_config(topic.name)
            differences = self.__get_topic_config_diff(
                topic_config_in_cluster, topic.config.configs
            )

            if differences:
                json_body: list[dict[str, str]] = []
                for difference in differences:
                    if difference.diff_type is DiffType.REMOVE:
                        json_body.append(
                            {"name": difference.key, "operation": "DELETE"}
                        )
                    elif config_value := difference.change.new_value:
                        json_body.append(
                            {"name": difference.key, "value": config_value}
                        )
                await self.kafka_rest.batch_alter_topic_config(topic.name, json_body)

            else:
                log.info(
                    "Config of topic didn't change. Skipping update.",
                    topic_name=topic.name,
                )
        except TopicNotFoundException:
            await self.kafka_rest.create_topic(topic_spec)

    @staticmethod
    def __check_partition_count(
        topic_in_cluster: TopicResponse,
        topic_spec: TopicSpec,
        broker_config: dict[str, str],
    ) -> None:
        topic_name = topic_in_cluster.topic_name
        partition_count = topic_in_cluster.partitions_count
        if partition_count == (
            topic_spec.partitions_count or int(broker_config["num.partitions"])
        ):
            log.debug(
                "Topic partition count did not change. Updating configs.",
                topic_name=topic_name,
                partition_count=partition_count,
            )
        else:
            msg = f"Topic Creation: partition count of topic {topic_name} changed! Partitions count of topic {topic_name} is {partition_count}. The given partitions count {topic_spec.partitions_count}."
            raise TopicTransactionError(msg)

    @staticmethod
    def __check_replication_factor(
        topic_in_cluster: TopicResponse,
        topic_spec: TopicSpec,
        broker_config: dict[str, str],
    ) -> None:
        topic_name = topic_in_cluster.topic_name
        replication_factor = topic_in_cluster.replication_factor
        if replication_factor == (
            topic_spec.replication_factor
            or int(broker_config["default.replication.factor"])
        ):
            log.debug(
                "Topic replication factor did not change. Updating configs.",
                topic_name=topic_name,
                replication_factor=replication_factor,
            )
        else:
            msg = f"Topic Creation: replication factor of topic {topic_name} changed! Replication factor of topic {topic_name} is {replication_factor}. The given replication count {topic_spec.replication_factor}."
            raise TopicTransactionError(msg)

    async def __dry_run_topic_deletion(self, topic_name: str) -> None:
        try:
            topic_in_cluster = await self.kafka_rest.get_topic(topic_name)
            log.info(
                magentaify(
                    f"Topic Deletion: topic {topic_in_cluster.topic_name} exists in the cluster. Deleting topic."
                )
            )
        except TopicNotFoundException:
            log.warning(
                "Topic does not exist in the cluster and cannot be deleted. Skipping.",
                topic_name=topic_name,
            )

    async def __execute_topic_deletion(self, topic_name: str) -> None:
        try:
            await self.kafka_rest.get_topic(topic_name)
            await self.kafka_rest.delete_topic(topic_name)
        except TopicNotFoundException:
            log.warning(
                "Topic does not exist in the cluster and cannot be deleted. Skipping.",
                topic_name=topic_name,
            )

    @classmethod
    def __prepare_body(cls, topic: KafkaTopic) -> TopicSpec:
        """Prepare the POST request body needed for the topic creation.

        :param topic_name: The name of the topic
        :param topic_config: The topic config
        :return: Topic specification
        """
        topic_spec_json: dict[str, Any] = topic.config.model_dump(
            include={
                "partitions_count": True,
                "replication_factor": True,
                "configs": True,
            },
            exclude_none=True,
        )
        configs: list[dict[str, Any]] = []
        for config_name, config_value in topic_spec_json["configs"].items():
            configs.append({"name": config_name, "value": config_value})
        topic_spec_json["configs"] = configs
        topic_spec_json["topic_name"] = topic.name
        return TopicSpec.model_validate(topic_spec_json)
