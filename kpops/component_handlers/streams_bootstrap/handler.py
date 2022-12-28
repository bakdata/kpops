from __future__ import annotations

import logging

# TODO: Move to config
from pathlib import Path
from typing import TYPE_CHECKING

from kpops.component_handlers.streams_bootstrap.helm_wrapper import (
    HelmCommandConfig,
    HelmWrapper,
)
from kpops.component_handlers.streams_bootstrap.streams_bootstrap_application_type import (
    ApplicationType,
)

if TYPE_CHECKING:
    from kpops.cli.pipeline_config import PipelineConfig

log = logging.getLogger("StreamsBootstrapApp")


class AppHandler:
    def __init__(self, helm_wrapper: HelmWrapper):
        self._helm_wrapper = helm_wrapper
        helm_wrapper.helm_repo_add()

    def install_app(
        self,
        release_name: str,
        namespace: str,
        values: dict,
        app_type: ApplicationType,
        dry_run: bool,
        local_chart_path: Path | None = None,
    ):
        """
        Calls helm upgrade
        :param release_name: The release name of your chart
        :param namespace: The namespace where the chart is going to be released
        :param values: The value YAML for the chart
        :param app_type: The type of the application
        :param dry_run: sets the --dry-run flag
        """
        self._helm_wrapper.helm_upgrade_install(
            release_name=release_name,
            namespace=namespace,
            values=values,
            app=app_type.value,
            dry_run=dry_run,
            local_chart_path=local_chart_path,
        )

    def uninstall_app(
        self,
        release_name: str,
        namespace: str,
        dry_run: bool,
        suffix: str = "",
    ):
        """
        Uninstalls a streams or producer app and installs the cleanup job
        :param release_name: The release name of your chart
        :param namespace: The namespace where the chart is going to be released
        :param values: The value YAML for the chart
        :param app_type: The type of the application
        :param dry_run: Sets the --dry-run flag
        :param suffix: Suffix to be provided to helm_uninstall()
        """

        try:
            self._helm_wrapper.helm_uninstall(
                namespace=namespace,
                release_name=release_name,
                dry_run=dry_run,
                suffix=suffix,
            )
        except Exception as e:
            if len(e.args) == 1 and "release: not found" in e.args[0]:
                log.info("Could not find release, nothing to uninstall.")
            else:
                raise e

    def clean_app(
        self,
        release_name: str,
        namespace: str,
        values: dict,
        app_type: ApplicationType,
        dry_run: bool,
        delete_outputs: bool = False,
        retain_clean_jobs: bool = False,
    ):
        """
        Cleans an app using the respective cleanup job
        :param dry_run: Dry run command
        :param delete_outputs: Whether output topics should be deleted
        :param release_name: The release name of the chart
        :param namespace: The namespace where the cleanup job is released to
        :param values: The value YAML for the chart
        :param app_type: The type of the application
        :param delete_output_topics: Whether to delete output topics with the cleanup job
        :return:
        """
        suffix = "-clean"
        log.info(f"Uninstall old cleanup job for {release_name}")
        self.uninstall_app(
            release_name=release_name,
            namespace=namespace,
            dry_run=dry_run,
            suffix=suffix,
        )

        log.info(f"Init cleanup job for {release_name}")
        values["streams"]["deleteOutput"] = delete_outputs
        self._helm_wrapper.helm_upgrade_install(
            release_name=release_name,
            namespace=namespace,
            values=values,
            app=app_type.value,
            dry_run=dry_run,
            suffix=suffix,
            helm_command_config=HelmCommandConfig(wait=True, wait_for_jobs=True),
        )
        if not retain_clean_jobs:
            log.info(f"Uninstall cleanup job for {release_name}")
            self.uninstall_app(
                release_name=release_name,
                namespace=namespace,
                dry_run=dry_run,
                suffix=suffix,
            )

    @classmethod
    def from_pipeline_config(cls, pipeline_config: PipelineConfig):
        return cls(
            helm_wrapper=HelmWrapper(
                helm_config=pipeline_config.streams_bootstrap_helm_config
            )
        )
