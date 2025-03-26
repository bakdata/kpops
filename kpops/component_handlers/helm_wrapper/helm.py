from __future__ import annotations

import asyncio
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, final

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
from kpops.manifests.kubernetes import KubernetesManifest

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


log = logging.getLogger("Helm")


@final
class Helm:
    _version: Version = None
    _repos: map[str, str] = {}

    def __init__(self, helm_config: HelmConfig) -> None:
        Helm._context = helm_config.context
        Helm._debug = helm_config.debug
        Helm._version = Helm.get_version()
        if Helm._version.major != 3:
            msg = f"The supported Helm version is 3.x.x. The current Helm version is {self._version.major}.{self._version.minor}.{self._version.patch}"
            raise RuntimeError(msg)

    def add_repo(
        self,
        repository_name: str,
        repository_url: str,
        repo_auth_flags: RepoAuthFlags | None = None,
    ) -> None:
        if Helm._repos.get(repository_name) == repository_url:
            log.debug(
                f"Repository {repository_name} already added, skipping helm command."
            )
            return
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
            Helm._repos[repository_name] = repository_url
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

    async def upgrade_install(
        self,
        release_name: str,
        chart: str,
        dry_run: bool,
        namespace: str,
        values: dict[str, Any],
        flags: HelmUpgradeInstallFlags | None = None,
    ) -> str:
        """Prepare and execute the `helm upgrade --install` command."""
        if flags is None:
            flags = HelmUpgradeInstallFlags()
        with tempfile.NamedTemporaryFile("w", delete=False) as values_file:
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
            return await self.__async_execute(command)

    async def uninstall(
        self,
        namespace: str,
        release_name: str,
        dry_run: bool,
    ) -> str | None:
        """Prepare and execute the `helm uninstall` command."""
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
            return await self.__async_execute(command)
        except ReleaseNotFoundException:
            log.warning(
                f"Release with name {release_name} not found. Could not uninstall app."
            )

    async def get_values(
        self,
        namespace: str,
        release_name: str,
    ) -> dict[str, Any] | None:
        """Prepare and execute the `helm get values` command."""
        command = [
            "helm",
            "get",
            "values",
            release_name,
            "--namespace",
            namespace,
            "--output",
            "yaml",
        ]
        try:
            command_result = await self.__async_execute(command)
            return yaml.safe_load(command_result)
        except ReleaseNotFoundException:
            log.warning(
                f"Release with name {release_name} not found. Could not get values."
            )

    @staticmethod
    def template(
        release_name: str,
        chart: str,
        namespace: str,
        values: dict[str, Any],
        flags: HelmTemplateFlags | None = None,
    ) -> tuple[KubernetesManifest, ...]:
        """From Helm: Render chart templates locally and display the output.

        Any values that would normally be looked up or retrieved in-cluster will
        be faked locally. Additionally, none of the server-side testing of chart
        validity (e.g. whether an API is supported) is done.

        :param str release_name: the release name for which the command is ran
        :param chart: Helm chart to be templated
        :param namespace: The Kubernetes namespace the command should execute in
        :param values: `values.yaml` to be used
        :param flags: the flags to be set for `helm template`, defaults to HelmTemplateFlags()
        :return: the rendered resource (list of Kubernetes manifests)
        """
        if flags is None:
            flags = HelmTemplateFlags()
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as values_file:
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
            output = Helm.__execute(command)
            manifests = KubernetesManifest.from_yaml(output)
            return tuple(manifests)

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

    @staticmethod
    def get_version() -> Version:
        if Helm._version is None:
            command = ["helm", "version", "--short"]
            short_version = Helm.__execute(command)
            version_match = re.search(r"^v(\d+(?:\.\d+){0,2})", short_version)
            if version_match is None:
                msg = f"Could not parse the Helm version.\n\nHelm output:\n{short_version}"
                raise RuntimeError(msg)
            version = map(int, version_match.group(1).split("."))
            Helm._version = Version(*version)

        return Helm._version

    @staticmethod
    def load_manifest(yaml_contents: str) -> Iterator[HelmTemplate]:
        is_beginning: bool = False
        template_name = None
        current_yaml_doc: list[str] = []
        for line in HelmChart(yaml_contents):
            if line.startswith("---"):
                is_beginning = True
                if template_name and current_yaml_doc:
                    manifests = KubernetesManifest.from_yaml(
                        "\n".join(current_yaml_doc)
                    )
                    manifest = next(manifests)  # only 1 manifest
                    yield HelmTemplate(Path(template_name), manifest)
                    template_name = None
                    current_yaml_doc.clear()
            elif is_beginning:
                template_name = HelmTemplate.parse_source(line)
                is_beginning = False
            else:
                current_yaml_doc.append(line)

    @staticmethod
    def __execute(command: list[str]) -> str:
        command = Helm.__set_global_flags(command)
        log.debug(f"Executing {' '.join(command)}")
        process = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        Helm.parse_helm_command_stderr_output(process.stderr)
        log.debug(process.stdout)
        return process.stdout

    @staticmethod
    async def __async_execute(command: list[str]):
        command = Helm.__set_global_flags(command)
        log.debug(f"Executing {' '.join(command)}")
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()
        Helm.parse_helm_command_stderr_output(stderr.decode())
        log.debug(stdout)
        return stdout.decode()

    @staticmethod
    def __set_global_flags(command: list[str]) -> list[str]:
        if Helm._context:
            log.debug(f"Changing the Kubernetes context to {Helm._context}")
            command.extend(["--kube-context", Helm._context])
        if Helm._debug:
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
