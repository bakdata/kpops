from __future__ import annotations

import logging
from abc import ABC
from typing import Self

from typing_extensions import override

from kpops.component_handlers import get_handlers
from kpops.components.base_components.cleaner import Cleaner
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.config import get_config
from kpops.utils.dict_ops import update_nested

log = logging.getLogger("KafkaApp")


class KafkaAppCleaner(Cleaner, ABC):
    """Helm app for resetting and cleaning a streams-bootstrap app."""

    from_: None = None  # pyright: ignore[reportIncompatibleVariableOverride]
    to: None = None  # pyright: ignore[reportIncompatibleVariableOverride]

    @classmethod
    def from_parent(cls, parent: KafkaApp) -> Self:
        parent_kwargs = parent.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude={"_cleaner", "from_", "to"},
        )
        # enrichment: cleaner defaults take precedence over parent
        cleaner_defaults = cls.extend_with_defaults(name=parent.name)
        kwargs = update_nested(cleaner_defaults, parent_kwargs)
        cleaner = cls(**kwargs)
        cleaner.values.name_override = None
        return cleaner

    @property
    @override
    def helm_chart(self) -> str:
        raise NotImplementedError

    @override
    async def clean(self, dry_run: bool) -> None:
        """Clean an app using a cleanup job.

        :param dry_run: Dry run command
        """
        log.info(f"Uninstall old cleanup job for {self.helm_release_name}")
        await self.destroy(dry_run)

        log.info(f"Deploy cleanup job for {self.helm_release_name}")
        await self.deploy(dry_run)

        if not get_config().retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {self.helm_release_name}")
            await self.destroy(dry_run)


class KafkaApp(PipelineComponent, ABC):
    """Base component for Kafka-based components."""

    @override
    async def deploy(self, dry_run: bool) -> None:
        if self.to:
            for topic in self.to.kafka_topics:
                await get_handlers().topic_handler.create_topic(topic, dry_run=dry_run)

            if schema_handler := get_handlers().schema_handler:
                await schema_handler.submit_schemas(to_section=self.to, dry_run=dry_run)

        await super().deploy(dry_run)
