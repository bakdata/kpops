from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml
from pydantic import BaseModel, Field

from kpops.component_handlers.helm_wrapper.exception import ParseError
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfig, DescConfig


class HelmDiffConfig(BaseModel):
    ignore: set[str] = Field(
        default_factory=set,
        description="Set of keys that should not be checked.",
        example="- name\n- imageTag",
    )


class RepoAuthFlags(BaseModel):
    """Authorisation-related flags for `helm repo`

    :param username: Username, defaults to None
    :type username: str, optional
    :param password: Password, defaults to None
    :type password: str, optional
    :param ca_file: Certificate file, defaults to None
    :type ca_file: Path, optional
    :param insecure_skip_tls_verify: If true, Kubernetes API server's certificate will not be checked for validity
        , defaults to False
    :type insecure_skip_tls_verify: bool, optional
    """

    username: str | None = Field(
        default=None, description=describe_attr("username", __doc__)
    )
    password: str | None = Field(
        default=None, description=describe_attr("password", __doc__)
    )
    ca_file: Path | None = Field(
        default=None, description=describe_attr("ca_file", __doc__)
    )
    insecure_skip_tls_verify: bool = Field(
        default=False, description=describe_attr("insecure_skip_tls_verify", __doc__)
    )

    class Config(CamelCaseConfig, DescConfig):
        pass


class HelmRepoConfig(BaseModel):
    """Helm repository configuration

    :param repository_name: Name of the Helm repository
    :type repository_name: str
    :param url: URL to the Helm repository
    :type url: str
    :param repo_auth_flags: Authorisation-related flags
    :type repo_auth_flags: RepoAuthFlags
    """

    repository_name: str = Field(
        default=..., description=describe_attr("repository_name", __doc__)
    )
    url: str = Field(default=..., description=describe_attr("url", __doc__))
    repo_auth_flags: RepoAuthFlags = Field(
        default=RepoAuthFlags(), description=describe_attr("repo_auth_flags", __doc__)
    )

    class Config(CamelCaseConfig, DescConfig):
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

        :Example:

        # Source: chart/templates/serviceaccount.yaml
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
HELM_MANIFEST = "MANIFEST:\n"


@dataclass(frozen=True)
class HelmChart:
    content: str

    def __iter__(self) -> Iterator[str]:
        yield from self.manifest.splitlines()
        yield "---"  # add final divider to make parsing easier

    @property
    def manifest(self) -> str:
        """
        Reads the manifest section of Helm stdout. `helm upgrade --install` output message contains three sections
        in the following order:

        - HOOKS
        - MANIFEST
        - NOTES (optional)

        The content of the manifest is used to create the diff. If a NOTES.txt exists in the Helm chart, the NOTES
        section will be included in the output.

        :return: The content of the manifest section
        """
        if HELM_MANIFEST not in self.content:
            raise ParseError(f"Failed to parse Helm stdout:\n {self.content}")

        manifest_start = self.content.index(HELM_MANIFEST) + len(HELM_MANIFEST)
        manifest_end = (
            self.content.index(HELM_NOTES) if HELM_NOTES in self.content else -1
        )

        return self.content[manifest_start:manifest_end]


@dataclass(frozen=True)
class Version:
    major: int
    minor: int = 0
    patch: int = 0
