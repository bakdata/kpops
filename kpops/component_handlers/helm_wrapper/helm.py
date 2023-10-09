from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from typing import TYPE_CHECKING

import yaml

from kpops.component_handlers.helm_wrapper.exception import ReleaseNotFoundException
from kpops.component_handlers.helm_wrapper.model import (
    HelmChart,
    HelmConfig,
    HelmTemplate,
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
    Version,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

log = logging.getLogger("Helm")


class Helm:
    def __init__(self, helm_config: HelmConfig) -> None:
        self._context = helm_config.context
        self._debug = helm_config.debug
        self._version = self.get_version()
        if self._version.major != 3:
            msg = f"The supported Helm version is 3.x.x. The current Helm version is {self._version.major}.{self._version.minor}.{self._version.patch}"
            raise RuntimeError(msg)

    def add_repo(
        self,
        repository_name: str,
        repository_url: str,
        repo_auth_flags: RepoAuthFlags | None = None,
    ) -> None:
        if repo_auth_flags is None:
            repo_auth_flags = RepoAuthFlags()
        command = [
            "helm",
            "repo",
            "add",
            repository_name,
            repository_url,
        ]
        command.extend(repo_auth_flags.to_command())

        try:
            self.__execute(command)
        except (ReleaseNotFoundException, RuntimeError) as e:
            if (
                len(e.args) == 1
                and re.match(
                    "Error: repository name (.*) already exists, please specify a different name",
                    e.args[0],
                )
                is not None
            ):
                log.exception(f"Could not add repository {repository_name}.")
            else:
                raise

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
        flags: HelmUpgradeInstallFlags | None = None,
    ) -> str:
        """Prepare and execute the `helm upgrade --install` command."""
        if flags is None:
            flags = HelmUpgradeInstallFlags()
        with tempfile.NamedTemporaryFile("w") as values_file:
            yaml.safe_dump(values, values_file)

            command = [
                "helm",
                "upgrade",
                release_name,
                chart,
                "--install",
                "--namespace",
                namespace,
                "--values",
                values_file.name,
            ]
            command.extend(flags.to_command())
            if dry_run:
                command.append("--dry-run")
            return self.__execute(command)

    def uninstall(
        self,
        namespace: str,
        release_name: str,
        dry_run: bool,
    ) -> str | None:
        """Prepare and execute the helm uninstall command."""
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
        flags: HelmTemplateFlags | None = None,
    ) -> str:
        """From HELM: Render chart templates locally and display the output.

        Any values that would normally be looked up or retrieved in-cluster will
        be faked locally. Additionally, none of the server-side testing of chart
        validity (e.g. whether an API is supported) is done.

        :param str release_name: the release name for which the command is ran
        :param chart: Helm chart to be templated
        :param namespace: The Kubernetes namespace the command should execute in
        :param values: `values.yaml` to be used
        :param flags: the flags to be set for `helm template`, defaults to HelmTemplateFlags()
        :return: the output of `helm template`
        """
        if flags is None:
            flags = HelmTemplateFlags()
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
            command.extend(flags.to_command())
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
            msg = f"Could not parse the Helm version.\n\nHelm output:\n{short_version}"
            raise RuntimeError(msg)
        version = map(int, version_match.group(1).split("."))
        return Version(*version)

    @staticmethod
    def load_manifest(yaml_contents: str) -> Iterator[HelmTemplate]:
        is_beginning: bool = False
        template_name = None
        current_yaml_doc: list[str] = []
        for line in HelmChart(yaml_contents):
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

    def __execute(self, command: list[str]) -> str:
        command = self.__set_global_flags(command)
        log.debug(f"Executing {' '.join(command)}")
        process = subprocess.run(
            command,
            check=True,
            capture_output=True,
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
                raise ReleaseNotFoundException
            elif "error" in lower:
                raise RuntimeError(stderr)
            elif "warning" in lower:
                log.warning(line)
