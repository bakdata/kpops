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
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
    Version,
    YamlReader,
)

log = logging.getLogger("Helm")


class Helm:
    def __init__(self, helm_config: HelmConfig) -> None:
        self._context = helm_config.context
        self._debug = helm_config.debug
        self._version = self.get_version()
        if self._version.major != 3:
            raise RuntimeError(
                f"The supported Helm version is 3.x.x. The current Helm version is {self._version.major}.{self._version.minor}.{self._version.patch}"
            )

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

        if self._version.minor > 7:
            self.__execute(["helm", "repo", "update", repository_name])
        else:
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
        """Prepares and executes the `helm upgrade --install` command"""
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
        """Prepares and executes the helm uninstall command"""
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

    def template(
        self,
        release_name: str,
        chart: str,
        namespace: str,
        values: dict,
        flags: HelmTemplateFlags = HelmTemplateFlags(),
    ) -> str:
        """From HELM: Render chart templates locally and display the output.

        Any values that would normally be looked up or retrieved in-cluster will
        be faked locally. Additionally, none of the server-side testing of chart
        validity (e.g. whether an API is supported) is done.

        :param str release_name: the release name for which the command is ran
        :type release_name: str
        :param chart: Helm chart to be templated
        :type chart: str
        :param namespace: The Kubernetes namespace the command should execute in
        :type namespace: str
        :param values: `values.yaml` to be used
        :type values: dict
        :param flags: the flags to be set for `helm template`, defaults to HelmTemplateFlags()
        :type flags: HelmTemplateFlags, optional
        :return: the output of `helm template`
        :rtype: str
        """
        with tempfile.NamedTemporaryFile("w") as values_file:
            yaml.safe_dump(values, values_file)
            command = [
                "helm",
                "template",
                release_name,
                chart,
                "--namespace",
                namespace,
                "--values",
                values_file.name,
            ]
            command = Helm.__enrich_template_command(command, flags)
            return self.__execute(command)

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
            return Helm.load_manifest(stdout)
        except ReleaseNotFoundException:
            return ()

    def get_version(self) -> Version:
        command = ["helm", "version", "--short"]
        short_version = self.__execute(command)
        version_match = re.search(r"^v(\d+(?:\.\d+){0,2})", short_version)
        if version_match is None:
            raise RuntimeError(
                f"Could not parse the Helm version.\n\nHelm output:\n{short_version}"
            )
        version = map(int, version_match.group(1).split("."))
        return Version(*version)

    @staticmethod
    def load_manifest(yaml_contents: str) -> Iterator[HelmTemplate]:
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
    def __enrich_template_command(
        command: list[str],
        helm_command_config: HelmTemplateFlags,
    ) -> list[str]:
        """
        Enrich `self.template()` with the flags to be used for `helm template`

        :param list[str] command: command that contains a call to
            `helm template` with specified release name, chart and values
        :param helm_command_config: flags to be set
        :type helm_command_config: HelmTemplateFlags
        :return: the enriched with flags `helm template`
        :rtype: list[str]
        """
        if helm_command_config.api_version:
            command.extend(["--api-versions", helm_command_config.api_version])
        if helm_command_config.ca_file:
            command.extend(["--ca-file", helm_command_config.ca_file])
        if helm_command_config.cert_file:
            command.extend(["--cert-file", helm_command_config.cert_file])
        if helm_command_config.version:
            command.extend(["--version", helm_command_config.version])
        return command

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
        if helm_command_config.create_namespace:
            command.append("--create-namespace")
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
