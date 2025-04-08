from __future__ import annotations

import logging
from functools import cached_property
from typing import Annotated, Any

import pydantic
from pydantic import Field, computed_field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.dry_run_handler import DryRunHandler
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmFlags,
    HelmRepoConfig,
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import (
    create_helm_name_override,
    create_helm_release_name,
)
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppValues,
)
from kpops.config import get_config
from kpops.core.operation import OperationMode
from kpops.manifests.argo import ArgoSyncWave, enrich_annotations
from kpops.manifests.kubernetes import K8S_LABEL_MAX_LEN, KubernetesManifest
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import SkipGenerate

log = logging.getLogger("HelmApp")


class HelmAppValues(KubernetesAppValues):
    """Helm app values.

    :param name_override: Helm chart name override, assigned automatically
    :param fullname_override: Helm chart fullname override, assigned automatically
    """

    name_override: (
        Annotated[str, pydantic.StringConstraints(max_length=K8S_LABEL_MAX_LEN)] | None
    ) = Field(
        default=None,
        title="NameOverride",
        description=describe_attr("name_override", __doc__),
    )
    fullname_override: (
        Annotated[str, pydantic.StringConstraints(max_length=K8S_LABEL_MAX_LEN)] | None
    ) = Field(
        default=None,
        title="FullnameOverride",
        description=describe_attr("fullname_override", __doc__),
    )

    # TODO(Ivan Yordanov): Replace with a function decorated with `@model_serializer`
    # BEWARE! All default values are enforced, hard to replicate without
    # access to ``model_dump``
    @override
    def model_dump(self, **_: Any) -> dict[str, Any]:
        return super().model_dump(
            by_alias=True, exclude_none=True, exclude_defaults=True
        )


class HelmApp(KubernetesApp):
    """Kubernetes app managed through Helm with an associated Helm chart.

    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to None this means that the command "helm repo add" is not called and Helm
        expects a path to local Helm chart.
    :param diff_config: Helm diff config
    :param version: Helm chart version, defaults to None
    :param values: Helm app values
    """

    repo_config: SkipGenerate[HelmRepoConfig | None] = Field(
        default=None,
        description=describe_attr("repo_config", __doc__),
    )
    diff_config: SkipGenerate[HelmDiffConfig] = Field(
        default=HelmDiffConfig(),
        description=describe_attr("diff_config", __doc__),
    )
    version: str | None = Field(
        default=None,
        description=describe_attr("version", __doc__),
    )
    values: HelmAppValues = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        description=describe_attr("values", __doc__),
    )

    @cached_property
    def _helm(self) -> Helm:
        """Helm object that contains component-specific config such as repo."""
        helm = Helm(get_config().helm_config)
        if self.repo_config is not None:
            helm.add_repo(
                self.repo_config.repository_name,
                self.repo_config.url,
                self.repo_config.repo_auth_flags,
            )
        return helm

    @cached_property
    def _helm_diff(self) -> HelmDiff:
        """Helm diff object of last and current release of this component."""
        return HelmDiff(self.diff_config)

    @cached_property
    def _dry_run_handler(self) -> DryRunHandler:
        return DryRunHandler(self._helm, self._helm_diff, self.namespace)

    @computed_field  # NOTE: we want to see them in the generate output
    @property
    def helm_release_name(self) -> str:
        """The name for the Helm release."""
        return create_helm_release_name(self.full_name)

    @computed_field  # NOTE: we want to see them in the generate output
    @property
    def helm_name_override(self) -> str:
        """Helm chart name override."""
        return create_helm_name_override(self.full_name)

    @property
    def helm_chart(self) -> str:
        """Return component's Helm chart."""
        msg = (
            f"Please implement the helm_chart property of the {self.__module__} module."
        )
        raise NotImplementedError(msg)

    @property
    def helm_flags(self) -> HelmFlags:
        """Return shared flags for Helm commands."""
        auth_flags = (
            self.repo_config.repo_auth_flags.model_dump() if self.repo_config else {}
        )
        return HelmFlags(
            **auth_flags,
            version=self.version,
            create_namespace=get_config().create_namespace,
        )

    @property
    def template_flags(self) -> HelmTemplateFlags:
        """Return flags for Helm template command."""
        return HelmTemplateFlags(
            **self.helm_flags.model_dump(),
            api_version=get_config().helm_config.api_version,
        )

    @override
    def manifest_deploy(self) -> tuple[KubernetesManifest, ...]:
        values = self.to_helm_values()
        if get_config().operation_mode is OperationMode.ARGO:
            sync_wave = ArgoSyncWave(sync_wave=1)
            values = enrich_annotations(values, sync_wave.key, sync_wave.value)

        return self._helm.template(
            self.helm_release_name,
            self.helm_chart,
            self.namespace,
            values,
            self.template_flags,
        )

    @property
    def deploy_flags(self) -> HelmUpgradeInstallFlags:
        """Return flags for Helm upgrade install command."""
        return HelmUpgradeInstallFlags.model_validate(self.helm_flags.model_dump())

    @override
    async def deploy(self, dry_run: bool) -> None:
        stdout = await self._helm.upgrade_install(
            self.helm_release_name,
            self.helm_chart,
            dry_run,
            self.namespace,
            self.to_helm_values(),
            self.deploy_flags,
        )
        if dry_run:
            self._dry_run_handler.print_helm_diff(stdout, self.helm_release_name, log)

    @override
    async def destroy(self, dry_run: bool) -> None:
        stdout = await self._helm.uninstall(
            self.namespace,
            self.helm_release_name,
            dry_run,
        )

        if stdout:
            log.info(magentaify(stdout))

    def to_helm_values(self) -> dict[str, Any]:
        """Generate a dictionary of values readable by Helm from `self.values`.

        :returns: The values to be used by Helm
        """
        name_override = self.helm_name_override
        if self.values.name_override is None:
            self.values.name_override = name_override
        if self.values.fullname_override is None:
            self.values.fullname_override = name_override
        return self.values.model_dump()

    def print_helm_diff(self, stdout: str) -> None:
        """Print the diff of the last and current release of this component.

        :param stdout: The output of a Helm command that installs or upgrades the release
        """
        current_release = list(
            self._helm.get_manifest(self.helm_release_name, self.namespace)
        )
        if current_release:
            log.info(f"Helm release {self.helm_release_name} already exists")
        else:
            log.info(f"Helm release {self.helm_release_name} does not exist")
        new_release = Helm.load_manifest(stdout)
        self._helm_diff.log_helm_diff(log, current_release, new_release)
