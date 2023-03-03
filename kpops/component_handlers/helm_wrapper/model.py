from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml
from pydantic import BaseModel, Field

from kpops.utils.pydantic import CamelCaseConfig


class HelmDiffConfig(BaseModel):
    enable: bool = Field(
        default=True,
        description="Enable Helm Diff.",
    )
    ignore: set[str] = Field(
        default_factory=set,
        description="Set of keys that should not be checked.",
        example="- name\n- imageTag",
    )


class RepoAuthFlags(BaseModel):
    username: str | None = None
    password: str | None = None
    ca_file: Path | None = None
    insecure_skip_tls_verify: bool = False

    class Config(CamelCaseConfig):
        pass


class HelmRepoConfig(BaseModel):
    repository_name: str
    url: str
    repo_auth_flags: RepoAuthFlags = Field(default=RepoAuthFlags())

    class Config(CamelCaseConfig):
        pass


class HelmConfig(BaseModel):
    context: str | None = Field(
        default=None,
        description="Set the name of the kubeconfig context. (--kube-context)",
        example="dev-storage",
    )
    debug: bool = Field(
        default=False,
        description="Run Helm in Debug mode.",
    )


@dataclass
class HelmUpgradeInstallFlags:
    create_namespace: bool = False
    force: bool = False
    repo_auth_flags: RepoAuthFlags = field(default_factory=RepoAuthFlags)
    timeout: str = "5m0s"
    version: str | None = None
    wait: bool = True
    wait_for_jobs: bool = False


HELM_SOURCE_PREFIX = "# Source: "


@dataclass
class HelmTemplateFlags:
    api_version: str | None = None
    ca_file: str | None = None
    cert_file: str | None = None
    version: str | None = None


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

    @classmethod
    def load(cls, filepath: str, content: str):
        template = yaml.load(content, yaml.Loader)
        return cls(filepath, template)


# Indicates the beginning of `NOTES:` section in the output of `helm install` or
# `helm upgrade`
HELM_NOTES = "\n\nNOTES:\n"


@dataclass
class YamlReader:
    content: str

    def __iter__(self) -> Iterator[str]:
        # discard all output before template documents
        start = self.content.index("---")
        if HELM_NOTES in self.content:
            end = self.content.index(HELM_NOTES)
        else:
            end = -1
        self.content = self.content[start:end]
        yield from self.content.splitlines()
        yield "---"  # add final divider to make parsing easier
