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
    def __init__(self, helm_config: HelmConfig) -> None:
        self._context = helm_config.context
        self._debug = helm_config.debug

    def add_repo(
        self,
        repository_name: str,
        repository_url: str,
        repo_auth_flags: RepoAuthFlags = RepoAuthFlags(),
    ) -> None:
        command = [
            "helm",
            "repo",
            "add",
            repository_name,
            repository_url,
        ]

        if repo_auth_flags.username and repo_auth_flags.password:
            command.extend(
                [
                    "--username",
                    repo_auth_flags.username,
                    "--password",
                    repo_auth_flags.password,
                ]
            )

        command = Helm.__extend_tls_config(command, repo_auth_flags)

        try:
            self.__execute(command)
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

        self.__execute(["helm", "repo", "update"])

    def upgrade_install(
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
        with tempfile.NamedTemporaryFile("w") as values_file:
            yaml.safe_dump(values, values_file)

            command = ["helm"]
            command.extend(
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
            command = Helm.__extend_tls_config(command, flags.repo_auth_flags)

            command = Helm.__enrich_upgrade_install_command(command, dry_run, flags)
            return self.__execute(command)

    def uninstall(
        self,
        namespace: str,
        release_name: str,
        dry_run: bool,
    ) -> str | None:
        """
        Prepares and executes the helm uninstall command
        """
        command = [
            "helm",
            "uninstall",
            release_name,
            "--namespace",
            namespace,
        ]
        if dry_run:
            command.append("--dry-run")
        try:
            return self.__execute(command)
        except ReleaseNotFoundException:
            log.warning(
                f"Release with name {release_name} not found. Could not uninstall app."
            )

    def get_manifest(self, release_name: str, namespace: str) -> Iterable[HelmTemplate]:
        command = [
            "helm",
            "get",
            "manifest",
            release_name,
            "--namespace",
            namespace,
        ]

        try:
            stdout = self.__execute(command=command)
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

    @staticmethod
    def __extend_tls_config(
        command: list[str], repo_auth_flags: RepoAuthFlags
    ) -> list[str]:
        if repo_auth_flags.ca_file:
            command.extend(["--ca-file", str(repo_auth_flags.ca_file)])
        if repo_auth_flags.insecure_skip_tls_verify:
            command.append("--insecure-skip-tls-verify")
        return command

    @staticmethod
    def __enrich_upgrade_install_command(
        command: list[str],
        dry_run: bool,
        helm_command_config: HelmUpgradeInstallFlags,
    ) -> list[str]:
        if dry_run:
            command.append("--dry-run")
        if helm_command_config.force:
            command.append("--force")
        if helm_command_config.wait:
            command.append("--wait")
        if helm_command_config.wait_for_jobs:
            command.append("--wait-for-jobs")
        if helm_command_config.version:
            command.extend(["--version", helm_command_config.version])
        return command

    def __execute(self, command: list[str]) -> str:
        command = self.__set_global_flags(command)
        log.debug(f"Executing {' '.join(command)}")
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        Helm.parse_helm_command_stderr_output(process.stderr)
        log.debug(process.stdout)
        return process.stdout

    def __set_global_flags(self, command: list[str]) -> list[str]:
        if self._context:
            log.debug(f"Changing the Kubernetes context to {self._context}")
            command.extend(["--kube-context", self._context])
        if self._debug:
            log.debug("Enabling verbose mode.")
            command.append("--debug")
        return command

    @staticmethod
    def parse_helm_command_stderr_output(stderr: str) -> None:
        for line in stderr.splitlines():
            lower = line.lower()
            if "release: not found" in lower:
                raise ReleaseNotFoundException()
            elif "error" in lower:
                raise RuntimeError(stderr)
            elif "warning" in lower:
                log.warning(line)
