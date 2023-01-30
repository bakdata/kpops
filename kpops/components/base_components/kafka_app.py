from __future__ import annotations

import logging
from typing import ClassVar, Literal

from pydantic import BaseModel, Extra, Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import trim_release_name
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppConfig,
)
from kpops.utils.pydantic import CamelCaseConfig
from kpops.utils.yaml_loading import substitute

log = logging.getLogger("KafkaApp")


class KafkaStreamsConfig(BaseModel):
    brokers: str
    schema_registry_url: str | None = None

    class Config(CamelCaseConfig):
        extra = Extra.allow


class KafkaAppConfig(KubernetesAppConfig):
    streams: KafkaStreamsConfig
    name_override: str | None


class KafkaApp(KubernetesApp):
    """
    Base component for Kafka-based components.
    Producer or streaming apps should inherit from this class.
    """

    type: ClassVar[str] = "kafka-app"
    schema_type: Literal["kafka-app"] = Field(  # type: ignore[assignment]
        default="kafka-app", exclude=True
    )
    app: KafkaAppConfig
    repo_config: HelmRepoConfig = HelmRepoConfig(
        repository_name="bakdata-streams-bootstrap",
        url="https://bakdata.github.io/streams-bootstrap/",
    )
    version = "2.7.0"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.app.streams.brokers = substitute(
            self.app.streams.brokers, {"broker": self.config.broker}
        )
        if self.app.streams.schema_registry_url:
            self.app.streams.schema_registry_url = substitute(
                self.app.streams.schema_registry_url,
                {"schema_registry_url": self.config.schema_registry_url},
            )

    @property
    def clean_up_helm_chart(self) -> str:
        raise NotImplementedError()

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

    def _run_clean_up_job(
        self,
        values: dict,
        dry_run: bool,
        retain_clean_jobs: bool = False,
    ) -> None:
        """
        Cleans an app using the respective cleanup job
        :param values: The value YAML for the chart
        :param dry_run: Dry run command
        :param retain_clean_jobs: Whether to retain the cleanup job
        :return:
        """
        suffix = "-clean"
        clean_up_release_name = trim_release_name(
            self.helm_release_name + suffix, suffix
        )
        log.info(f"Uninstall old cleanup job for {clean_up_release_name}")

        self.__uninstall_clean_up_job(clean_up_release_name, dry_run)

        log.info(f"Init cleanup job for {clean_up_release_name}")

        stdout = self.__install_clean_up_job(
            clean_up_release_name, suffix, values, dry_run
        )

        if dry_run and self.helm_diff.config.enable:
            current_release = self.helm.get_manifest(
                clean_up_release_name, self.namespace
            )
            new_release = Helm.load_helm_manifest(stdout)
            self.helm_diff.get_diff(current_release, new_release)

        if not retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {clean_up_release_name}")
            self.__uninstall_clean_up_job(clean_up_release_name, dry_run)

    def __uninstall_clean_up_job(self, release_name: str, dry_run: bool) -> None:
        self.helm.uninstall(self.namespace, release_name, dry_run)

    def __install_clean_up_job(
        self,
        release_name: str,
        suffix: str,
        values: dict,
        dry_run: bool,
    ) -> str:
        clean_up_release_name = trim_release_name(release_name, suffix)
        return self.helm.upgrade_install(
            clean_up_release_name,
            self.clean_up_helm_chart,
            dry_run,
            self.namespace,
            values,
            HelmUpgradeInstallFlags(
                version=self.version,
                wait=True,
                wait_for_jobs=True,
            ),
        )
