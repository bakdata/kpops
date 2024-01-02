from __future__ import annotations

import logging
from abc import ABC

from pydantic import ConfigDict, Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.model import (
    HelmFlags,
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
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


class StreamsBootstrapHelmApp(HelmApp, ABC):
    repo_config: HelmRepoConfig = Field(
        default=HelmRepoConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://bakdata.github.io/streams-bootstrap/",
        ),
        description=describe_attr("repo_config", __doc__),
    )


class KafkaAppCleaner(StreamsBootstrapHelmApp):
    @property
    @override
    def helm_chart(self) -> str:
        raise NotImplementedError

    @property
    @override
    def helm_release_name(self) -> str:
        suffix = "-clean"
        return create_helm_release_name(self.full_name + suffix, suffix)

    @property
    @override
    def helm_flags(self) -> HelmFlags:
        return HelmUpgradeInstallFlags(
            create_namespace=self.config.create_namespace,
            version=self.version,
            wait=True,
            wait_for_jobs=True,
        )

    def run(self, dry_run: bool) -> None:
        """Clean an app using the respective cleanup job.

        :param dry_run: Dry run command
        """
        log.info(f"Uninstall old cleanup job for {self.helm_release_name}")
        self.destroy(dry_run=dry_run)

        log.info(f"Init cleanup job for {self.helm_release_name}")
        self.deploy(dry_run=dry_run)

        if not self.config.retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {self.helm_release_name}")
            self.destroy(dry_run=dry_run)


class KafkaApp(StreamsBootstrapHelmApp, ABC):
    """Base component for Kafka-based components.

    Producer or streaming apps should inherit from this class.

    :param app: Application-specific settings
    :param version: Helm chart version, defaults to "2.9.0"
    """

    app: KafkaAppValues = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    version: str | None = Field(
        default="2.9.0",
        description=describe_attr("version", __doc__),
    )

    @override
    def deploy(self, dry_run: bool) -> None:
        if self.to:
            self.handlers.topic_handler.create_topics(
                to_section=self.to, dry_run=dry_run
            )

            if self.handlers.schema_handler:
                self.handlers.schema_handler.submit_schemas(
                    to_section=self.to, dry_run=dry_run
                )
        super().deploy(dry_run)
