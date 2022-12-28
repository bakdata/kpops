import logging

from kpops.component_handlers.topic.exception import TopicNotFoundException
from kpops.component_handlers.topic.model import (
    TopicConfigResponse,
    TopicResponse,
    TopicSpec,
)
from kpops.component_handlers.topic.proxy_wrapper import HEADERS, ProxyWrapper
from kpops.component_handlers.topic.utils import (
    get_effective_config,
    parse_and_compare_topic_configs,
    parse_rest_proxy_topic_config,
)
from kpops.components.base_components.models.to_section import TopicConfig, ToSection
from kpops.utils.colorify import greenify, magentaify, yellowify
from kpops.utils.dict_differ import Diff, DiffType, get_diff, render_diff

log = logging.getLogger("KafkaTopic")


class TopicHandler:
    def __init__(self, proxy_wrapper: ProxyWrapper):
        self.proxy_wrapper = proxy_wrapper

    def create_topics(self, to_section: ToSection, dry_run: bool) -> None:
        topics: dict[str, TopicConfig] = to_section.topics
        for topic_name, topic_config in topics.items():
            topic_spec = self.__prepare_body(topic_name, topic_config)
            if dry_run:
                self.__dry_run_topic_creation(topic_name, topic_spec, topic_config)
            else:
                try:
                    self.proxy_wrapper.get_topic(topic_name=topic_name)
                    topic_config_in_cluster = self.proxy_wrapper.get_topic_config(
                        topic_name=topic_name
                    )
                    differences = self.__get_topic_config_diff(
                        topic_config_in_cluster, topic_config.configs
                    )

                    if differences:
                        json_body = []
                        for difference in differences:
                            if difference.diff_type == DiffType.REMOVE:
                                json_body.append(
                                    {"name": difference.key, "operation": "DELETE"}
                                )
                            else:
                                config_value = difference.change.new_value
                                if config_value:
                                    json_body.append(
                                        {"name": difference.key, "value": config_value}
                                    )
                        self.proxy_wrapper.batch_alter_topic_config(
                            topic_name=topic_name,
                            json_body=json_body,
                        )

                    else:
                        log.info(
                            f"Topic Creation: config of topic {topic_name} didn't change. Skipping update."
                        )
                except TopicNotFoundException:
                    self.proxy_wrapper.create_topic(topic_spec=topic_spec)

    def delete_topics(self, to_section: ToSection, dry_run: bool) -> None:
        topics: dict[str, TopicConfig] = to_section.topics
        for topic_name in topics.keys():
            if dry_run:
                self.__dry_run_topic_deletion(topic_name=topic_name)
            else:
                try:
                    self.proxy_wrapper.get_topic(topic_name=topic_name)
                    self.proxy_wrapper.delete_topic(topic_name=topic_name)
                except TopicNotFoundException:
                    log.warning(
                        f"Topic Deletion: topic {topic_name} does not exist in the cluster and cannot be deleted. Skipping."
                    )

    @staticmethod
    def __get_topic_config_diff(
        cluster_config: TopicConfigResponse, current_config: dict
    ) -> list[Diff]:
        comparable_in_cluster_config_dict, _ = parse_rest_proxy_topic_config(
            cluster_config
        )

        return get_diff(comparable_in_cluster_config_dict, current_config)

    def __dry_run_topic_creation(
        self,
        topic_name: str,
        topic_spec: TopicSpec,
        topic_config: TopicConfig | None = None,
    ) -> None:
        try:
            topic_in_cluster = self.proxy_wrapper.get_topic(topic_name=topic_name)
            topic_name = topic_in_cluster.topic_name
            if topic_config:
                topic_config_in_cluster = self.proxy_wrapper.get_topic_config(
                    topic_name=topic_name
                )
                in_cluster_config, new_config = parse_and_compare_topic_configs(
                    topic_config_in_cluster, topic_config.configs
                )
                if diff := render_diff(in_cluster_config, new_config):
                    log.info(f"Config changes for topic {topic_name}:")
                    log.info("\n" + diff)

            log.info(f"Topic Creation: {topic_name} already exists in cluster.")
            log.debug("HTTP/1.1 400 Bad Request")
            log.debug(HEADERS)
            error_message = {
                "error_code": 40002,
                "message": f"Topic '{topic_name}' already exists.",
            }
            log.debug(error_message)

            broker_config = self.proxy_wrapper.get_broker_config()
            effective_config = get_effective_config(broker_config)

            self.__check_partition_count(topic_in_cluster, topic_spec, effective_config)
            self.__check_replication_factor(
                topic_in_cluster, topic_spec, effective_config
            )
        except TopicNotFoundException:
            log.info(
                greenify(
                    f"Topic Creation: {topic_name} does not exist in the cluster. Creating topic."
                )
            )
            log.debug(f"POST /clusters/{self.proxy_wrapper.cluster_id}/topics HTTP/1.1")
            log.debug(f"Host: {self.proxy_wrapper.host}")
            log.debug(HEADERS)
            log.debug(topic_spec.dict())

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
            log.info(
                yellowify(
                    f"Topic Creation: partition count of topic {topic_name} did not change. Current partitions count {partition_count}. Updating configs."
                )
            )
        else:
            log.error(
                f"Topic Creation: partition count of topic {topic_name} changed! Partitions count of topic {topic_name} is {partition_count}. The given partitions count {topic_spec.partitions_count}."
            )
            exit(1)

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
            log.info(
                yellowify(
                    f"Topic Creation: replication factor of topic {topic_name} did not change. Current replication factor {replication_factor}. Updating configs."
                )
            )
        else:
            log.error(
                f"Topic Creation: replication factor of topic {topic_name} changed! Replication factor of topic {topic_name} is {replication_factor}. The given replication count {topic_spec.replication_factor}."
            )
            exit(1)

    def __dry_run_topic_deletion(self, topic_name: str) -> None:
        try:
            topic_in_cluster = self.proxy_wrapper.get_topic(topic_name=topic_name)
            log.info(
                magentaify(
                    f"Topic Deletion: topic {topic_in_cluster.topic_name} exists in the cluster. Deleting topic."
                )
            )
            log.debug(
                f"DELETE /clusters/{self.proxy_wrapper.cluster_id}/topics HTTP/1.1"
            )
        except TopicNotFoundException:
            log.warning(
                f"Topic Deletion: topic {topic_name} does not exist in the cluster and cannot be deleted. Skipping."
            )
            log.debug(f"Host: {self.proxy_wrapper.host}")
            log.debug(HEADERS)
            log.debug("HTTP/1.1 404 Not Found")
            log.debug(HEADERS)
            error_message = {
                "error_code": 40403,
                "message": f"This server does not host the topic-partition '{topic_name}'.",
            }
            log.debug(error_message)

    @classmethod
    def __prepare_body(cls, topic_name: str, topic_config: TopicConfig) -> TopicSpec:
        """
        Prepares the POST request body needed for the topic creation
        :param topic_name: The name of the topic
        :param topic_config: The topic config
        :return:
        """
        topic_spec_json: dict = topic_config.dict(
            include={
                "partitions_count": True,
                "replication_factor": True,
                "configs": True,
            },
            exclude_unset=True,
            exclude_none=True,
        )
        configs = []
        for config_name, config_value in topic_spec_json["configs"].items():
            configs.append({"name": config_name, "value": config_value})
        topic_spec_json["configs"] = configs
        topic_spec_json["topic_name"] = topic_name
        return TopicSpec(**topic_spec_json)
