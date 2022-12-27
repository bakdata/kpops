from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmConfig,
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.component_handlers.helm_wrapper.utils import trim_release_name
from kpops.component_handlers.streams_bootstrap.streams_bootstrap_application_type import (
    ApplicationType,
)

if TYPE_CHECKING:
    from kpops.cli.pipeline_config import PipelineConfig

log = logging.getLogger("StreamsBootstrapApp")


class AppHandler:
    def __init__(
        self,
        helm_config: HelmConfig,
        helm_repo_config: HelmRepoConfig,
        helm_diff: HelmDiff,
    ):
        self._helm_wrapper = Helm(helm_config)
        self.repository_name = helm_repo_config.repository_name
        self.chart_version = helm_repo_config.version
        self._helm_wrapper.helm_repo_add(
            helm_repo_config.repository_name,
            helm_repo_config.url,
            RepoAuthFlags(
                username=helm_repo_config.username, password=helm_repo_config.password
            ),
        )
        self.helm_diff = helm_diff

    def install_app(
        self,
        release_name: str,
        application_type: ApplicationType,
        namespace: str,
        values: dict,
        dry_run: bool,
    ):
        """
        Calls helm upgrade
        :param release_name: The release name of your chart
        :param namespace: The namespace where the chart is going to be released
        :param values: The value YAML for the chart
        :param dry_run: sets the --dry-run flag
        """
        stdout = self._helm_wrapper.helm_upgrade_install(
            release_name=release_name,
            chart=f"{self.repository_name}/{application_type.value}",
            dry_run=dry_run,
            namespace=namespace,
            values=values,
            flags=HelmUpgradeInstallFlags(version=self.chart_version),
        )
        if dry_run and self.helm_diff.config.enable:
            current_release = self._helm_wrapper.helm_get_manifest(
                release_name, namespace
            )
            new_release = Helm.load_helm_manifest(stdout)
            helm_diff = HelmDiff.get_diff(current_release, new_release)
            self.helm_diff.log_helm_diff(helm_diff, log)

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

        release_name = trim_release_name(release_name, suffix)
        try:
            self._helm_wrapper.helm_uninstall(
                namespace=namespace,
                release_name=release_name,
                dry_run=dry_run,
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
        :param retain_clean_jobs: Whether to retain the cleanup job
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

        stdout = self._helm_wrapper.helm_upgrade_install(
            release_name=trim_release_name(release_name, suffix),
            chart=f"{self.repository_name}/{app_type.value}",
            dry_run=dry_run,
            namespace=namespace,
            values=values,
            flags=HelmUpgradeInstallFlags(
                version=self.chart_version, wait=True, wait_for_jobs=True
            ),
        )

        if dry_run and self.helm_diff.config.enable:
            current_release = self._helm_wrapper.helm_get_manifest(
                release_name, namespace
            )
            new_release = Helm.load_helm_manifest(stdout)
            self.helm_diff.get_diff(current_release, new_release)
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
            helm_config=pipeline_config.helm_config,
            helm_repo_config=pipeline_config.streams_bootstrap_helm_config,
            helm_diff=HelmDiff(pipeline_config.helm_diff_config),
        )
