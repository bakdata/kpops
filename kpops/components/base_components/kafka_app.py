from __future__ import annotations

import logging
from typing import Literal

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
from kpops.utils.docstring import describe_attr, describe_object
from kpops.utils.pydantic import CamelCaseConfig, DescConfig
from kpops.utils.yaml_loading import substitute

log = logging.getLogger("KafkaApp")


class KafkaStreamsConfig(BaseModel):
    """Kafka Streams config

    :param brokers: Brokers
    :type brokers: str
    :param schema_registry_url: URL of the schema registry, defaults to None
    :type schema_registry_url: str, None, optional
    """

    brokers: str = Field(default=..., description=describe_attr("brokers", __doc__))
    schema_registry_url: str | None = Field(
        default=None, description=describe_attr("schema_registry_url", __doc__)
    )

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.allow


class KafkaAppConfig(KubernetesAppConfig):
    """Settings specific to Kafka Apps

    :param streams: Kafka streams config
    :type streams: KafkaStreamsConfig
    :param name_override: Override name with this value, defaults to None
    :type name_override: str, None, optional
    """

    streams: KafkaStreamsConfig = Field(
        default=..., description=describe_attr("streams", __doc__)
    )
    name_override: str | None = Field(
        default=None, description=describe_attr("name_override", __doc__)
    )


class KafkaApp(KubernetesApp):
    """Base component for Kafka-based components.

    Producer or streaming apps should inherit from this class.

    :param type: Component type, defaults to "kafka-app"
    :type type: str, optional
    :param schema_type: Used for schema generation, same as :param:`type`,
        defaults to "kafka-app"
    :type schema_type: Literal["kafka-app"], optional
    :param app: Application-specific settings
    :type app: KafkaAppConfig
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component,
        defaults to HelmRepoConfig(repository_name="bakdata-streams-bootstrap", url="https://bakdata.github.io/streams-bootstrap/")
    :type repo_config: HelmRepoConfig, None, optional
    :param version: Helm chart version, defaults to "2.9.0"
    :type version: str, optional
    """

    type: str = Field(default="kafka-app", description="Component type")
    schema_type: Literal["kafka-app"] = Field(  # type: ignore[assignment]
        default="kafka-app",
        title="Component type",
        description=describe_object(__doc__),
        exclude=True,
    )
    app: KafkaAppConfig = Field(
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
    version = Field(
        default="2.9.0",
        description=describe_attr("version", __doc__),
    )

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
        """Helm chart used to destroy and clean this component"""
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
        """Clean an app using the respective cleanup job

        :param values: The value YAML for the chart
        :type values: dict
        :param dry_run: Dry run command
        :type dry_run: bool
        :param retain_clean_jobs: Whether to retain the cleanup job, defaults to False
        :type retain_clean_jobs: bool, optional
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
            new_release = Helm.load_manifest(stdout)
            self.helm_diff.log_helm_diff(log, current_release, new_release)

        if not retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {clean_up_release_name}")
            self.__uninstall_clean_up_job(clean_up_release_name, dry_run)

    def __uninstall_clean_up_job(self, release_name: str, dry_run: bool) -> None:
        """Uninstall clean up job

        :param release_name: Name of the Helm release
        :type release_name: str
        :param dry_run: Whether to do a dry run of the command
        :type dry_run: bool
        """
        self.helm.uninstall(self.namespace, release_name, dry_run)

    def __install_clean_up_job(
        self,
        release_name: str,
        suffix: str,
        values: dict,
        dry_run: bool,
    ) -> str:
        """Install clean up job

        :param release_name: Name of the Helm release
        :type release_name: str
        :param suffix: Suffix to add to the realease name, e.g. "-clean"
        :type suffix: str
        :param values: The Helm values for the chart
        :type values: dict
        :param dry_run: Whether to do a dry run of the command
        :type dry_run: bool
        :return: Install clean up job with helm, return the output of the installation
        :rtype: str
        """
        clean_up_release_name = trim_release_name(release_name, suffix)
        return self.helm.upgrade_install(
            clean_up_release_name,
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
