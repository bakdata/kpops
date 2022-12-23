from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from collections.abc import Iterator
from typing import Iterable

import yaml

from kpops.component_handlers.helm_wrapper.exception import ReleaseNotFoundException
from kpops.component_handlers.helm_wrapper.model import (
    HelmConfig,
    HelmTemplate,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
    YamlReader,
)

log = logging.getLogger("Helm")


class Helm:
    RELEASE_NAME_MAX_LEN = 53

    def __init__(self, helm_config: HelmConfig) -> None:
        self._context = helm_config.context
        self._debug = helm_config.debug

    @classmethod
    def trim_release_name(cls, name: str, suffix: str = "") -> str:
        if len(name) + len(suffix) > cls.RELEASE_NAME_MAX_LEN:
            new_name = name[: (cls.RELEASE_NAME_MAX_LEN - len(suffix))] + suffix
            log.critical(
                f"The Helm release name {name} is invalid. We shorten it to {cls.RELEASE_NAME_MAX_LEN} characters: \n {name + suffix} --> {new_name}"
            )
            name = new_name
        return name

    def helm_repo_add(
        self,
        repository_name: str,
        repository_url: str,
        repo_auth_flags: RepoAuthFlags = RepoAuthFlags(),
    ) -> None:
        bash_command = [
            "helm",
            "repo",
            "add",
            repository_name,
            repository_url,
        ]

        if repo_auth_flags.username and repo_auth_flags.password:
            bash_command.extend(
                [
                    "--username",
                    repo_auth_flags.username,
                    "--password",
                    repo_auth_flags.password,
                ]
            )

        bash_command = Helm.__extend_tls_config(bash_command, repo_auth_flags)

        try:
            self.__execute(bash_command, dry_run=False)
        except Exception as e:
            if (
                len(e.args) == 1
                and re.match(
                    "Error: repository name (.*) already exists, please specify a different name",
                    e.args[0],
                )
                is not None
            ):
                log.error(f"Could not add repository {repository_name}. {e}")
            else:
                raise e

        self.__execute(["helm", "repo", "update", repository_name], dry_run=False)

    def helm_upgrade_install(
        self,
        release_name: str,
        chart: str,
        dry_run: bool,
        namespace: str,
        values: dict,
        flags: HelmUpgradeInstallFlags = HelmUpgradeInstallFlags(),
    ) -> str:
        """
        Prepares and executes the helm upgrade install command
        """
        # TODO: Move out of the function
        # release_name = self.trim_release_name(release_name, suffix=suffix)
        with tempfile.NamedTemporaryFile("w") as values_file:
            yaml.safe_dump(values, values_file)

            bash_command = ["helm"]
            bash_command.extend(
                [
                    "upgrade",
                    release_name,
                    chart,
                    "--install",
                    f"--timeout={flags.timeout}",
                    "--namespace",
                    namespace,
                    "--values",
                    values_file.name,
                ]
            )
            bash_command = Helm.__extend_tls_config(bash_command, flags.repo_auth_flags)

            bash_command = Helm.__enrich_upgrade_install_command(
                bash_command, dry_run, flags
            )
            try:
                return self.__execute(bash_command, dry_run=dry_run)

                # TODO: should go out of this method
                # if dry_run and self._helm_config.diff.enable:
                #     current_release = self.helm_get_manifest(release_name, namespace)
                #     new_release = Helm.load_helm_manifest(stdout)
                #     self._helm_diff(current_release, new_release)

            except Exception as e:
                log.error(f"Could not install chart. More details: {e}")
                exit(1)

    def helm_uninstall(
        self,
        namespace: str,
        release_name: str,
        dry_run: bool,
    ) -> str:
        """
        Prepares and executes the helm uninstall command
        """
        bash_command = [
            "helm",
            "uninstall",
            release_name,
            "--namespace",
            namespace,
        ]
        if dry_run:
            bash_command.append("--dry-run")
        try:
            return self.__execute(bash_command, dry_run=dry_run)
        except ReleaseNotFoundException:
            log.warning(f"Release not found {release_name}. Could not uninstall app.")
            exit(1)
        except RuntimeError as runtime_error:
            log.error(
                f"Could not uninstall app {release_name}. More details: {runtime_error}"
            )
            exit(1)

    def helm_get_manifest(
        self, release_name: str, namespace: str
    ) -> Iterable[HelmTemplate]:
        bash_command = [
            "helm",
            "get",
            "manifest",
            release_name,
            "--namespace",
            namespace,
        ]

        try:
            stdout = self.__execute(command=bash_command, dry_run=True)
            return Helm.load_helm_manifest(stdout)
        except ReleaseNotFoundException:
            return ()

    @staticmethod
    def load_helm_manifest(yaml_contents: str) -> Iterator[HelmTemplate]:
        is_beginning: bool = False
        template_name = None
        current_yaml_doc: list[str] = []
        for line in YamlReader(yaml_contents):
            if line.startswith("---"):
                is_beginning = True
                if template_name and current_yaml_doc:
                    yield HelmTemplate.load(template_name, "\n".join(current_yaml_doc))
                    template_name = None
                    current_yaml_doc.clear()
            elif is_beginning:
                template_name = HelmTemplate.parse_source(line)
                is_beginning = False
            else:
                current_yaml_doc.append(line)

    # TODO: Move out of class
    # def _helm_diff(
    #     self,
    #     current_release: Iterable[HelmTemplate],
    #     new_release: Iterable[HelmTemplate],
    # ) -> list[tuple[dict, dict]]:
    #     new_release_index = {
    #         helm_template.filepath: helm_template for helm_template in new_release
    #     }
    #
    #     changes: list[tuple[dict, dict]] = []
    #     # collect changed & deleted files
    #     for current_resource in current_release:
    #         # get corresponding dry-run release
    #         new_resource = new_release_index.pop(current_resource.filepath, None)
    #         changes.append(
    #             (
    #                 current_resource.template,
    #                 new_resource.template if new_resource else {},
    #             )
    #         )
    #
    #     # collect added files
    #     for new_resource in new_release_index.values():
    #         changes.append(({}, new_resource.template))
    #
    #     for before, after in changes:
    #         if diff := render_diff(
    #             before,
    #             after,
    #             ignore=self._helm_config.diff.ignore,
    #         ):
    #             log.info("\n" + diff)
    #     return changes

    @staticmethod
    def __extend_tls_config(
        bash_command: list[str], repo_auth_flags: RepoAuthFlags
    ) -> list[str]:
        if repo_auth_flags.ca_file:
            bash_command.extend(["--ca-file", str(repo_auth_flags.ca_file)])
        if repo_auth_flags.insecure_skip_tls_verify:
            bash_command.append("--insecure-skip-tls-verify")
        return bash_command

    @staticmethod
    def __enrich_upgrade_install_command(
        bash_command: list[str],
        dry_run: bool,
        helm_command_config: HelmUpgradeInstallFlags,
    ) -> list[str]:
        if dry_run:
            bash_command.append("--dry-run")
        if helm_command_config.force:
            bash_command.append("--force")
        if helm_command_config.wait:
            bash_command.append("--wait")
        if helm_command_config.wait_for_jobs:
            bash_command.append("--wait-for-jobs")
        if helm_command_config.version:
            bash_command.extend(["--version", helm_command_config.version])
        return bash_command

    def __execute(self, command: list[str], *, dry_run: bool) -> str:
        command = self.__set_global_flags(command)
        log.debug(f"Executing {' '.join(command)}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        exit_code = process.wait()
        stdout, stderr = process.communicate()
        if stdout and (not dry_run or exit_code != 0):
            log.info(stdout)

        Helm.parse_helm_command_stderr_output(stderr)
        return stdout

    def __set_global_flags(self, bash_command: list[str]) -> list[str]:
        if self._context:
            log.debug(f"Changing the Kubernetes context to {self._context}")
            bash_command.extend(["--kube-context", self._context])
        if self._debug:
            log.debug("Enabling verbose mode.")
            bash_command.append("--debug")
        return bash_command

    @staticmethod
    def parse_helm_command_stderr_output(stderr: str) -> None:
        for line in stderr.splitlines():
            lower = line.lower()
            if "release: not found" in lower:
                raise ReleaseNotFoundException()
            elif "error" in lower:
                raise RuntimeError(stderr)
            elif "warning" in lower:
                log.info(line)

    @classmethod
    def __check_release_name_length(cls, release_name: str):
        if len(release_name) > cls.RELEASE_NAME_MAX_LEN:
            log.error(f"Invalid value: The {release_name} is more than 52 characters.")
            exit(1)
