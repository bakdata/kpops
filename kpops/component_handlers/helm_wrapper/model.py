from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from pydantic import ConfigDict, Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.exception import ParseError
from kpops.manifests.kubernetes import KubernetesManifest
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import (
    DescConfigModel,
    SerializeAsOptional,
    SerializeAsOptionalModel,
)

KeyPath = tuple[str, ...]


class HelmDiffConfig(SerializeAsOptionalModel):
    ignore: SerializeAsOptional[list[KeyPath]] = Field(
        default=[],  # pyright: ignore[reportUnknownArgumentType]
        description="List of keypaths that should be excluded from the diff.",
        examples=[("name",), ("imageTag",), ("metadata", "labels", "helm.sh/chart")],
    )


class RepoAuthFlags(DescConfigModel):
    """Authorisation-related flags for `helm repo`.

    :param username: Username, defaults to None
    :param password: Password, defaults to None
    :param ca_file: Path to CA bundle file to verify certificates of HTTPS-enabled servers, defaults to None
    :param cert_file: Path to SSL certificate file to identify HTTPS client, defaults to None
    :param insecure_skip_tls_verify: If true, Kubernetes API server's certificate will not be checked for validity
        , defaults to False
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
    cert_file: Path | None = Field(
        default=None, description=describe_attr("cert_file", __doc__)
    )
    insecure_skip_tls_verify: bool = Field(
        default=False, description=describe_attr("insecure_skip_tls_verify", __doc__)
    )

    def to_command(self) -> list[str]:
        command: list[str] = []
        if self.username:
            command.extend(["--username", self.username])
        if self.password:
            command.extend(["--password", self.password])
        if self.ca_file:
            command.extend(["--ca-file", str(self.ca_file)])
        if self.cert_file:
            command.extend(["--cert-file", str(self.cert_file)])
        if self.insecure_skip_tls_verify:
            command.append("--insecure-skip-tls-verify")
        return command


class HelmRepoConfig(DescConfigModel):
    """Helm repository configuration.

    :param repository_name: Name of the Helm repository
    :param url: URL to the Helm repository
    :param repo_auth_flags: Authorisation-related flags
    """

    repository_name: str = Field(description=describe_attr("repository_name", __doc__))
    url: str = Field(description=describe_attr("url", __doc__))
    repo_auth_flags: RepoAuthFlags = Field(
        default=RepoAuthFlags(), description=describe_attr("repo_auth_flags", __doc__)
    )


class HelmConfig(DescConfigModel):
    """Global Helm configuration.

    :param context: Name of kubeconfig context (`--kube-context`)
    :param debug: Run Helm in Debug mode
    :param api_version: Kubernetes API version used for `Capabilities.APIVersions`
    """

    context: str | None = Field(
        default=None,
        description=describe_attr("context", __doc__),
        examples=["dev-storage"],
    )
    debug: bool = Field(
        default=False,
        description=describe_attr("debug", __doc__),
    )
    api_version: str | None = Field(
        default=None,
        title="API version",
        description=describe_attr("api_version", __doc__),
    )


class HelmFlags(RepoAuthFlags):
    set_file: dict[str, Path] = Field(default_factory=dict)
    create_namespace: bool = False
    version: str | None = None
    force: bool = False
    timeout: str = "5m0s"
    wait: bool = True
    wait_for_jobs: bool = False

    model_config: ClassVar[ConfigDict] = ConfigDict(
        extra="allow",
    )

    @override
    def to_command(self) -> list[str]:
        command = super().to_command()
        if self.set_file:
            command.extend(
                [
                    "--set-file",
                    ",".join([f"{key}={path}" for key, path in self.set_file.items()]),
                ]
            )
        if self.create_namespace:
            command.append("--create-namespace")
        if self.version:
            command.extend(["--version", self.version])
        if self.force:
            command.append("--force")
        if self.timeout:
            command.extend(["--timeout", self.timeout])
        if self.wait:
            command.append("--wait")
        if self.wait_for_jobs:
            command.append("--wait-for-jobs")
        return command


class HelmUpgradeInstallFlags(HelmFlags): ...


class HelmTemplateFlags(HelmFlags):
    api_version: str | None = None

    @override
    def to_command(self) -> list[str]:
        command = super().to_command()
        if self.api_version:
            command.extend(["--api-versions", self.api_version])
        return command


HELM_SOURCE_PREFIX = "# Source: "


@dataclass
class HelmTemplate:
    filepath: Path
    manifest: KubernetesManifest

    @staticmethod
    def parse_source(source: str) -> str:
        """Parse source path from comment at the beginning of the YAML doc.

        :Example:
        .. code-block:: yaml
            # Source: chart/templates/serviceaccount.yaml
        """
        if not source.startswith(HELM_SOURCE_PREFIX):
            msg = "Not a valid Helm template source"
            raise ParseError(msg)
        return source.removeprefix(HELM_SOURCE_PREFIX).strip()


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
        """Reads the manifest section of Helm stdout.

        `helm upgrade --install` output message contains three sections in the following order:

        - HOOKS
        - MANIFEST
        - NOTES (optional)

        The content of the manifest is used to create the diff. If a NOTES.txt exists in the Helm chart, the NOTES
        section will be included in the output.

        It is important to note that the `helm get manifest` command only returns the manifests without the MANIFEST
        header in the stdout. Instead, the output starts with `---`.

        :return: The content of the manifest section
        """
        manifest_start = (
            self.content.index(HELM_MANIFEST) + len(HELM_MANIFEST)
            if HELM_MANIFEST in self.content
            else self.content.index("---")
        )

        manifest_end = (
            self.content.index(HELM_NOTES) if HELM_NOTES in self.content else -1
        )

        return self.content[manifest_start:manifest_end]


@dataclass(frozen=True)
class Version:
    major: int
    minor: int = 0
    patch: int = 0
