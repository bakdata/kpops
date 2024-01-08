from __future__ import annotations

import logging
from abc import ABC

from pydantic import ConfigDict, Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
from kpops.components.base_components.models.from_section import (
    FromTopic,
    InputTopicTypes,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfigModel, DescConfigModel

log = logging.getLogger("KafkaApp")


class KafkaStreamsConfig(CamelCaseConfigModel, DescConfigModel):
    """Kafka Streams config.

    :param brokers: Brokers
    :param schema_registry_url: URL of the schema registry, defaults to None
    """

    brokers: str = Field(default=..., description=describe_attr("brokers", __doc__))
    schema_registry_url: str | None = Field(
        default=None, description=describe_attr("schema_registry_url", __doc__)
    )

    model_config = ConfigDict(
        extra="allow",
    )


class KafkaAppValues(HelmAppValues):
    """Settings specific to Kafka Apps.

    :param streams: Kafka streams config
    """

    streams: KafkaStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )


class KafkaApp(HelmApp, ABC):
    """Base component for Kafka-based components.

    Producer or streaming apps should inherit from this class.

    :param to: Topic(s) into which the component will write output,
        defaults to None
    :param app: Application-specific settings
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component,
        defaults to HelmRepoConfig(repository_name="bakdata-streams-bootstrap", url="https://bakdata.github.io/streams-bootstrap/")
    :param version: Helm chart version, defaults to "2.9.0"
    """

    to: ToSection | None = Field(
        default=None,
        description=describe_attr("to", __doc__),
    )
    app: KafkaAppValues = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    repo_config: HelmRepoConfig = Field(
        default=HelmRepoConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://bakdata.github.io/streams-bootstrap/",
        ),
        description=describe_attr("repo_config", __doc__),
    )
    version: str | None = Field(
        default="2.9.0",
        description=describe_attr("version", __doc__),
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_input_topics()
        self.set_output_topics()

    def add_input_topics(self, topics: list[str]) -> None:
        """Add given topics to the list of input topics.

        :param topics: Input topics
        """

    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        """Add given extra topics that share a role to the list of extra input topics.

        :param topics: Extra input topics
        :param role: Topic role
        """

    def set_input_pattern(self, name: str) -> None:
        """Set input pattern.

        :param name: Input pattern name
        """

    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        """Add an input pattern of type extra.

        :param role: Custom identifier belonging to one or multiple topics
        :param topic: Topic name
        """

    def set_output_topic(self, topic_name: str) -> None:
        """Set output topic.

        :param topic_name: Output topic name
        """

    def set_error_topic(self, topic_name: str) -> None:
        """Set error topic.

        :param topic_name: Error topic name
        """

    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        """Add an output topic of type extra.

        :param topic_name: Output topic name
        :param role: Role that is unique to the extra output topic
        """

    def set_input_topics(self) -> None:
        """Put values of config.from into the streams config section of streams bootstrap.

        Supports extra_input_topics (topics by role) or input_topics.
        """
        if self.from_:
            for name, topic in self.from_.topics.items():
                self.apply_from_inputs(name, topic)

    def apply_from_inputs(self, name: str, topic: FromTopic) -> None:
        """Add a `from` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        match topic.type:
            case None if topic.role:
                self.add_extra_input_topics(topic.role, [name])
            case InputTopicTypes.PATTERN if topic.role:
                self.add_extra_input_pattern(topic.role, name)
            case InputTopicTypes.PATTERN:
                self.set_input_pattern(name)
            case _:
                self.add_input_topics([name])

    def set_output_topics(self) -> None:
        """Put values of config.to into the producer config section of streams bootstrap.

        Supports extra_output_topics (topics by role) or output_topics.
        """
        if self.to:
            for topic in self.to.kafka_topics:
                self.apply_to_outputs(topic.name, topic.config)

    def apply_to_outputs(self, name: str, topic: TopicConfig) -> None:
        """Add a `to` section input to the component config.

        :param name: Name of the field
        :param topic: Value of the field
        """
        match topic.type:
            case None if topic.role:
                self.add_extra_output_topic(name, topic.role)
            case OutputTopicTypes.ERROR:
                self.set_error_topic(name)
            case _:
                self.set_output_topic(name)

    def weave_from_topics(
        self,
        to: ToSection | None,
        from_topic: FromTopic | None = None,
    ) -> None:
        """Weave output topics of upstream component or from component into config.

        Override this method to apply custom logic
        """
        if from_topic is None:
            from_topic = FromTopic(type=InputTopicTypes.INPUT)
        if not to:
            return
        input_topics = [
            topic.name
            for topic in to.kafka_topics
            if topic.config.type != OutputTopicTypes.ERROR and not topic.config.role
        ]
        for input_topic in input_topics:
            self.apply_from_inputs(input_topic, from_topic)

    @property
    def clean_up_helm_chart(self) -> str:
        """Helm chart used to destroy and clean this component."""
        raise NotImplementedError

    @override
    def deploy(self, dry_run: bool) -> None:
        if self.to:
            for topic in self.to.kafka_topics:
                topic.deploy(dry_run)

            # if self.handlers.schema_handler:
            #     self.handlers.schema_handler.submit_schemas(
            #         to_section=self.to, dry_run=dry_run
            #     )
        super().deploy(dry_run)

    def _run_clean_up_job(
        self,
        values: dict,
        dry_run: bool,
        retain_clean_jobs: bool = False,
    ) -> None:
        """Clean an app using the respective cleanup job.

        :param values: The value YAML for the chart
        :param dry_run: Dry run command
        :param retain_clean_jobs: Whether to retain the cleanup job, defaults to False
        """
        log.info(f"Uninstall old cleanup job for {self.clean_release_name}")

        self.__uninstall_clean_up_job(self.clean_release_name, dry_run)

        log.info(f"Init cleanup job for {self.clean_release_name}")

        stdout = self.__install_clean_up_job(self.clean_release_name, values, dry_run)

        if dry_run:
            self.dry_run_handler.print_helm_diff(stdout, self.clean_release_name, log)

        if not retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {self.clean_release_name}")
            self.__uninstall_clean_up_job(self.clean_release_name, dry_run)

    def __uninstall_clean_up_job(self, release_name: str, dry_run: bool) -> None:
        """Uninstall clean up job.

        :param release_name: Name of the Helm release
        :param dry_run: Whether to do a dry run of the command
        """
        self.helm.uninstall(self.namespace, release_name, dry_run)

    def __install_clean_up_job(
        self,
        release_name: str,
        values: dict,
        dry_run: bool,
    ) -> str:
        """Install clean up job.

        :param release_name: Name of the Helm release
        :param suffix: Suffix to add to the release name, e.g. "-clean"
        :param values: The Helm values for the chart
        :param dry_run: Whether to do a dry run of the command
        :return: Return the output of the installation
        """
        return self.helm.upgrade_install(
            release_name,
            self.clean_up_helm_chart,
            dry_run,
            self.namespace,
            values,
            HelmUpgradeInstallFlags(
                create_namespace=self.config.create_namespace,
                version=self.version,
                wait=True,
                wait_for_jobs=True,
            ),
        )
