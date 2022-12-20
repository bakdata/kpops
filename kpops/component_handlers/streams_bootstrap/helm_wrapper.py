from __future__ import annotations

import logging
import re
import subprocess
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml
from pydantic import BaseModel, BaseSettings, Field

from kpops.component_handlers.streams_bootstrap.exception import (
    ReleaseNotFoundException,
)
from kpops.utils.dict_differ import render_diff

log = logging.getLogger("Helm")


class HelmDiffConfig(BaseModel):
    enable: bool = True
    ignore: set[str] = Field(
        default_factory=set,
        description="keypaths using dot-notation to exclude",
    )


class HelmConfig(BaseModel):
    repository_name: str
    url: str
    version: str | None = None
    context: str | None = None
    username: str | None = None
    password: str | None = None
    diff: HelmDiffConfig = HelmDiffConfig()
    namespace: str | None = None
    ca_file: Path | None = None
    insecure_skip_tls_verify: bool = False


class HelmCommandConfig(BaseSettings):
    debug: bool = False
    force: bool = False
    timeout: str = "5m0s"
    wait: bool = True
    wait_for_jobs: bool = False

    class Config:
        env_prefix = "HELM_COMMAND_CONFIG_"


HELM_SOURCE_PREFIX = "# Source: "


@dataclass
class HelmTemplate:
    filepath: str
    template: dict

    @staticmethod
    def parse_source(source: str) -> str:
        """Parse source path from comment at the beginning of the YAML doc.
        Example: # Source: chart/templates/serviceaccount.yaml
        """
        if not source.startswith(HELM_SOURCE_PREFIX):
            raise ValueError("Not a valid Helm template source")
        return source.removeprefix(HELM_SOURCE_PREFIX).strip()

    @staticmethod
    def load(filepath: str, content: str) -> HelmTemplate:
        template = HelmTemplate.__load_template(content)
        return HelmTemplate(filepath, template)

    @staticmethod
    def __load_template(content: str) -> dict:
        return yaml.load(content, yaml.Loader)


def load_helm_manifest(yaml_contents: str) -> Iterator[HelmTemplate]:
    @dataclass
    class YamlReader:
        content: str

        def __iter__(self) -> Iterator[str]:
            # discard all output before template documents
            index = self.content.index("---")
            self.content = self.content[index:-1]
            yield from self.content.splitlines()
            yield "---"  # add final divider to make parsing easier

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


class HelmWrapper:
    RELEASE_NAME_MAX_LEN = 53

    def __init__(self, helm_config: HelmConfig) -> None:
        self._helm_config = helm_config

    @classmethod
    def trim_release_name(cls, name: str, suffix: str = "") -> str:
        if len(name) + len(suffix) > cls.RELEASE_NAME_MAX_LEN:
            new_name = name[: (cls.RELEASE_NAME_MAX_LEN - len(suffix))] + suffix
            log.critical(
                f"The Helm release name {name} is invalid. We shorten it to {cls.RELEASE_NAME_MAX_LEN} characters: \n {name + suffix} --> {new_name}"
            )
            name = new_name
        return name

    def helm_repo_add(self) -> None:
        bash_command = [
            "helm",
            "repo",
            "add",
            self._helm_config.repository_name,
            self._helm_config.url,
        ]

        if self._helm_config.username and self._helm_config.password:
            bash_command.extend(
                [
                    "--username",
                    self._helm_config.username,
                    "--password",
                    self._helm_config.password,
                ]
            )

        bash_command = self.__extend_tls_config(bash_command)

        try:
            self.__run_command(bash_command, dry_run=False)
        except Exception as e:
            if (
                len(e.args) == 1
                and re.match(
                    "Error: repository name (.*) already exists, please specify a different name",
                    e.args[0],
                )
                is not None
            ):
                log.error(
                    f"Could not add repository {self._helm_config.repository_name}. {e}"
                )
            else:
                raise e

        self.__run_command(["helm", "repo", "update"], dry_run=False)

    @staticmethod
    def _helm_get_manifest(release_name: str, namespace: str) -> Iterable[HelmTemplate]:
        bash_command = [
            "helm",
            "get",
            "manifest",
            release_name,
            "--namespace",
            namespace,
        ]
        try:
            stdout = HelmWrapper.__run_command(bash_command, dry_run=True)
            return load_helm_manifest(stdout)
        except ReleaseNotFoundException:
            return ()

    def _helm_diff(
        self,
        current_release: Iterable[HelmTemplate],
        new_release: Iterable[HelmTemplate],
    ) -> list[tuple[dict, dict]]:
        new_release_index = {
            helm_template.filepath: helm_template for helm_template in new_release
        }

        changes: list[tuple[dict, dict]] = []
        # collect changed & deleted files
        for current_resource in current_release:
            # get corresponding dry-run release
            new_resource = new_release_index.pop(current_resource.filepath, None)
            changes.append(
                (
                    current_resource.template,
                    new_resource.template if new_resource else {},
                )
            )

        # collect added files
        for new_resource in new_release_index.values():
            changes.append(({}, new_resource.template))

        for before, after in changes:
            if diff := render_diff(
                before,
                after,
                ignore=self._helm_config.diff.ignore,
            ):
                log.info("\n" + diff)
        return changes

    def helm_upgrade_install(
        self,
        release_name: str,
        namespace: str,
        values: dict,
        app: str,
        dry_run: bool,
        local_chart_path: Path | None = None,
        suffix: str = "",
        helm_command_config: HelmCommandConfig = HelmCommandConfig(),
    ) -> None:
        """
        Prepares and executes the helm upgrade install command
        """
        release_name = self.trim_release_name(release_name, suffix=suffix)
        with tempfile.NamedTemporaryFile("w") as values_file:
            yaml.safe_dump(values, values_file)

            bash_command = ["helm"]
            chart = (
                f"{self._helm_config.repository_name}/{app}"
                if local_chart_path is None
                else str(local_chart_path)
            )
            bash_command.extend(
                [
                    "upgrade",
                    release_name,
                    chart,
                    "--install",
                    f"--timeout={helm_command_config.timeout}",
                    "--namespace",
                    namespace,
                    "--values",
                    values_file.name,
                ]
            )
            bash_command = self.__extend_tls_config(bash_command)

            bash_command = self.__enrich_upgrade_install_command(
                bash_command, dry_run, helm_command_config
            )
            try:
                stdout = self.__run_command(bash_command, dry_run=dry_run)
                if dry_run and self._helm_config.diff.enable:
                    current_release = HelmWrapper._helm_get_manifest(
                        release_name, namespace
                    )
                    new_release = load_helm_manifest(stdout)
                    self._helm_diff(current_release, new_release)

            except Exception as e:
                log.error(f"Could not install chart. More details: {e}")
                exit(1)

    def helm_uninstall(
        self, namespace: str, release_name: str, dry_run: bool, suffix: str = ""
    ) -> None:
        """
        Prepares and executes the helm uninstall command
        """
        bash_command = [
            "helm",
            "uninstall",
            "--namespace",
            namespace,
            self.trim_release_name(release_name, suffix=suffix),
        ]
        if self._helm_config.context:
            log.info(f"Uninstalling in k8s context {self._helm_config.context}")
            bash_command.extend(["--kube-context", self._helm_config.context])
        if dry_run:
            bash_command.append("--dry-run")
        try:
            self.__run_command(bash_command, dry_run=dry_run)
        except ReleaseNotFoundException:
            log.warning(f"Release not found {release_name}. Could not uninstall app.")
        except RuntimeError as runtime_error:
            log.error(
                f"Could not uninstall app {release_name}. More details: {runtime_error}"
            )
            exit(1)

    def __extend_tls_config(self, bash_command: list[str]) -> list[str]:
        if self._helm_config.ca_file:
            bash_command.extend(["--ca-file", str(self._helm_config.ca_file)])
        if self._helm_config.insecure_skip_tls_verify:
            bash_command.append("--insecure-skip-tls-verify")
        return bash_command

    def __enrich_upgrade_install_command(
        self,
        bash_command: list[str],
        dry_run: bool,
        helm_command_config: HelmCommandConfig,
    ) -> list[str]:
        if dry_run:
            bash_command.append("--dry-run")
        if helm_command_config.debug:
            bash_command.append("--debug")
        if helm_command_config.force:
            bash_command.append("--force")
        if helm_command_config.wait:
            bash_command.append("--wait")
        if helm_command_config.wait_for_jobs:
            bash_command.append("--wait-for-jobs")
        if self._helm_config.context:
            log.info(f"Deploying in k8s context {self._helm_config.context}")
            bash_command.extend(["--kube-context", self._helm_config.context])
        if self._helm_config.version:
            bash_command.extend(["--version", self._helm_config.version])
        return bash_command

    @classmethod
    def __run_command(cls, bash_command: list[str], *, dry_run: bool) -> str:
        log.debug(f"Executing {' '.join(bash_command)}")
        process = subprocess.Popen(
            bash_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        exit_code = process.wait()
        stdout, stderr = process.communicate()
        if stdout and (not dry_run or exit_code != 0):
            log.info(stdout)

        HelmWrapper.parse_helm_command_stderr_output(stderr)
        return stdout

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
