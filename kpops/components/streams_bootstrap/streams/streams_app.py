from pydantic import Field
from typing_extensions import override

from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.streams_bootstrap.app_type import AppType
from kpops.components.streams_bootstrap.streams.model import StreamsAppConfig
from kpops.utils.docstring import describe_attr


class StreamsApp(KafkaApp):
    """StreamsApp component that configures a streams bootstrap app.

    :param app: Application-specific settings
    """

    app: StreamsAppConfig = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )

    @override
    def add_input_topics(self, topics: list[str]) -> None:
        self.app.streams.add_input_topics(topics)

    @override
    def add_extra_input_topics(self, role: str, topics: list[str]) -> None:
        self.app.streams.add_extra_input_topics(role, topics)

    @override
    def set_input_pattern(self, name: str) -> None:
        self.app.streams.input_pattern = name

    @override
    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        self.app.streams.extra_input_patterns[role] = topic

    @override
    def set_output_topic(self, topic_name: str) -> None:
        self.app.streams.output_topic = topic_name

    @override
    def set_error_topic(self, topic_name: str) -> None:
        self.app.streams.error_topic = topic_name

    @override
    def add_extra_output_topic(self, topic_name: str, role: str) -> None:
        self.app.streams.extra_output_topics[role] = topic_name

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.STREAMS_APP.value}"

    @property
    @override
    def clean_up_helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.CLEANUP_STREAMS_APP.value}"

    @override
    def reset(self, dry_run: bool) -> None:
        self.__run_streams_clean_up_job(dry_run, delete_output=False)

    @override
    def clean(self, dry_run: bool) -> None:
        self.__run_streams_clean_up_job(dry_run, delete_output=True)

    def __run_streams_clean_up_job(self, dry_run: bool, delete_output: bool) -> None:
        """Run clean job for this Streams app.

        :param dry_run: Whether to do a dry run of the command
        :param delete_output: Whether to delete the output of the app that is being cleaned
        """
        values = self.to_helm_values()
        values["streams"]["deleteOutput"] = delete_output
        self._run_clean_up_job(
            values=values,
            dry_run=dry_run,
            retain_clean_jobs=self.config.retain_clean_jobs,
        )
