import logging
from functools import cached_property

from pydantic import Field, computed_field
from typing_extensions import override

from kpops.component_handlers.kubernetes.pvc_handler import PVCHandler
from kpops.components.base_components.helm_app import HelmApp
from kpops.components.base_components.kafka_app import KafkaApp, KafkaAppCleaner
from kpops.components.common.streams_bootstrap import StreamsBootstrap
from kpops.components.common.topic import KafkaTopic
from kpops.components.streams_bootstrap.app_type import AppType
from kpops.components.streams_bootstrap.streams.model import (
    StreamsAppValues,
)
from kpops.utils.docstring import describe_attr

log = logging.getLogger("StreamsApp")


class StreamsAppCleaner(KafkaAppCleaner):
    from_: None = None
    to: None = None
    values: StreamsAppValues

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.CLEANUP_STREAMS_APP.value}"

    @override
    async def clean(self, dry_run: bool) -> None:
        await super().clean(dry_run)
        if self.values.stateful_set and self.values.persistence.enabled:
            await self.clean_pvcs(dry_run)

    async def clean_pvcs(self, dry_run: bool) -> None:
        app_full_name = super(HelmApp, self).full_name
        pvc_handler = await PVCHandler.create(app_full_name, self.namespace)
        if dry_run:
            pvc_names = await pvc_handler.list_pvcs()
            log.info(f"Deleting the PVCs {pvc_names} for StatefulSet '{app_full_name}'")
        else:
            log.info(f"Deleting the PVCs for StatefulSet '{app_full_name}'")
            await pvc_handler.delete_pvcs()


class StreamsApp(KafkaApp, StreamsBootstrap):
    """StreamsApp component that configures a streams-bootstrap app.

    :param values: streams-bootstrap Helm values
    """

    values: StreamsAppValues = Field(
        default=...,
        description=describe_attr("values", __doc__),
    )

    @computed_field
    @cached_property
    def _cleaner(self) -> StreamsAppCleaner:
        return StreamsAppCleaner(
            **self.model_dump(by_alias=True, exclude={"_cleaner", "from_", "to"})
        )

    @property
    @override
    def input_topics(self) -> list[KafkaTopic]:
        return self.values.streams.input_topics

    @property
    @override
    def extra_input_topics(self) -> dict[str, list[KafkaTopic]]:
        return self.values.streams.extra_input_topics

    @property
    @override
    def output_topic(self) -> KafkaTopic | None:
        return self.values.streams.output_topic

    @property
    @override
    def extra_output_topics(self) -> dict[str, KafkaTopic]:
        return self.values.streams.extra_output_topics

    @override
    def add_input_topics(self, topics: list[KafkaTopic]) -> None:
        self.values.streams.add_input_topics(topics)

    @override
    def add_extra_input_topics(self, role: str, topics: list[KafkaTopic]) -> None:
        self.values.streams.add_extra_input_topics(role, topics)

    @override
    def set_input_pattern(self, name: str) -> None:
        self.values.streams.input_pattern = name

    @override
    def add_extra_input_pattern(self, role: str, topic: str) -> None:
        self.values.streams.extra_input_patterns[role] = topic

    @override
    def set_output_topic(self, topic: KafkaTopic) -> None:
        self.values.streams.output_topic = topic

    @override
    def set_error_topic(self, topic: KafkaTopic) -> None:
        self.values.streams.error_topic = topic

    @override
    def add_extra_output_topic(self, topic: KafkaTopic, role: str) -> None:
        self.values.streams.extra_output_topics[role] = topic

    @property
    @override
    def helm_chart(self) -> str:
        return f"{self.repo_config.repository_name}/{AppType.STREAMS_APP.value}"

    @override
    async def reset(self, dry_run: bool) -> None:
        self._cleaner.values.streams.delete_output = False
        await self._cleaner.clean(dry_run)

    @override
    async def clean(self, dry_run: bool) -> None:
        self._cleaner.values.streams.delete_output = True
        await self._cleaner.clean(dry_run)
