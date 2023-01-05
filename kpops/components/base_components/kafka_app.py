import logging

from pydantic import BaseModel, Extra

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmUpgradeInstallFlags
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
    nameOverride: str | None


class KafkaApp(KubernetesApp):
    """
    Base component for kafka-based components.
    Producer or streaming apps should inherit from this class.
    """

    _type = "kafka-app"
    app: KafkaAppConfig

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app.streams.brokers = substitute(
            self.app.streams.brokers, {"broker": self.config.broker}
        )
        if self.app.streams.schema_registry_url:
            self.app.streams.schema_registry_url = substitute(
                self.app.streams.schema_registry_url,
                {"schema_registry_url": self.config.schema_registry_url},
            )

    def get_clean_up_helm_chart(self):
        raise NotImplementedError()

    def deploy(self, dry_run: bool):
        if self.to:
            self.handlers.topic_handler.create_topics(
                to_section=self.to, dry_run=dry_run
            )

            if self.handlers.schema_handler:
                self.handlers.schema_handler.submit_schemas(
                    to_section=self.to, dry_run=dry_run
                )
        super().deploy(dry_run)

    def destroy(self, dry_run: bool, clean: bool, delete_outputs: bool) -> None:
        super().destroy(dry_run, clean, delete_outputs)

    def clean(self, dry_run: bool, delete_outputs: bool, clear_schemas: bool):
        if delete_outputs:
            # producer clean up job will delete output topics
            self.clean_app(
                values=self.to_helm_values(),
                dry_run=dry_run,
                delete_outputs=delete_outputs,
                retain_clean_jobs=self.config.retain_clean_jobs,
            )

            if self.to and self.handlers.schema_handler and clear_schemas:
                self.handlers.schema_handler.delete_schemas(self.to, dry_run)

    def clean_app(
        self,
        values: dict,
        dry_run: bool,
        delete_outputs: bool = False,
        retain_clean_jobs: bool = False,
    ):
        """
        Cleans an app using the respective cleanup job
        :param dry_run: Dry run command
        :param delete_outputs: Whether output topics should be deleted
        :param values: The value YAML for the chart
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
        values["streams"]["deleteOutput"] = delete_outputs

        stdout = self.__install_clean_up_job(
            dry_run, self.namespace, clean_up_release_name, suffix, values
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
        self, dry_run, namespace, release_name, suffix, values
    ) -> str:
        clean_up_release_name = trim_release_name(release_name, suffix)
        return self.helm.upgrade_install(
            clean_up_release_name,
            self.get_clean_up_helm_chart(),
            dry_run,
            namespace,
            values,
            HelmUpgradeInstallFlags(
                version=self.version,
                wait=True,
                wait_for_jobs=True,
            ),
        )
