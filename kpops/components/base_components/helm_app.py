from __future__ import annotations

import logging
from functools import cached_property
from typing import Annotated, Any

import pydantic
from pydantic import Field, model_serializer
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.dry_run_handler import DryRunHandler
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmFlags,
    HelmRepoConfig,
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import (
    create_helm_name_override,
    create_helm_release_name,
)
from kpops.component_handlers.kubernetes.model import K8S_LABEL_MAX_LEN
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppValues,
)
from kpops.components.base_components.models.resource import Resource
from kpops.config import get_config
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import exclude_by_name

log = logging.getLogger("HelmApp")


class HelmAppValues(KubernetesAppValues):
    """Helm app values.

    :param name_override: Helm chart name override, assigned automatically
    """

    name_override: (
        Annotated[str, pydantic.StringConstraints(max_length=K8S_LABEL_MAX_LEN)] | None
    ) = Field(
        default=None,
        title="Nameoverride",
        description=describe_attr("name_override", __doc__),
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
    :param version: Helm chart version, defaults to None
    :param values: Helm app values
    """

    repo_config: HelmRepoConfig | None = Field(
        default=None,
        description=describe_attr("repo_config", __doc__),
    )
    version: str | None = Field(
        default=None,
        description=describe_attr("version", __doc__),
    )
    values: HelmAppValues = Field(
        description=describe_attr("values", __doc__),
    )

    @cached_property
    def helm(self) -> Helm:
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
    def helm_diff(self) -> HelmDiff:
        """Helm diff object of last and current release of this component."""
        return HelmDiff(get_config().helm_diff_config)

    @cached_property
    def dry_run_handler(self) -> DryRunHandler:
        helm_diff = HelmDiff(get_config().helm_diff_config)
        return DryRunHandler(self.helm, helm_diff, self.namespace)

    @property
    def helm_release_name(self) -> str:
        """The name for the Helm release."""
        return create_helm_release_name(self.full_name)

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
    def manifest(self) -> Resource:
        return self.helm.template(
            self.helm_release_name,
            self.helm_chart,
            self.namespace,
            self.to_helm_values(),
            self.template_flags,
        )

    @property
    def deploy_flags(self) -> HelmUpgradeInstallFlags:
        """Return flags for Helm upgrade install command."""
        return HelmUpgradeInstallFlags(**self.helm_flags.model_dump())

    @override
    async def deploy(self, dry_run: bool) -> None:
        stdout = await self.helm.upgrade_install(
            self.helm_release_name,
            self.helm_chart,
            dry_run,
            self.namespace,
            self.to_helm_values(),
            self.deploy_flags,
        )
        if dry_run:
            self.dry_run_handler.print_helm_diff(stdout, self.helm_release_name, log)

    @override
    async def destroy(self, dry_run: bool) -> None:
        stdout = await self.helm.uninstall(
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
        if self.values.name_override is None:
            self.values.name_override = self.helm_name_override
        return self.values.model_dump()

    def print_helm_diff(self, stdout: str) -> None:
        """Print the diff of the last and current release of this component.

        :param stdout: The output of a Helm command that installs or upgrades the release
        """
        current_release = list(
            self.helm.get_manifest(self.helm_release_name, self.namespace)
        )
        if current_release:
            log.info(f"Helm release {self.helm_release_name} already exists")
        else:
            log.info(f"Helm release {self.helm_release_name} does not exist")
        new_release = Helm.load_manifest(stdout)
        self.helm_diff.log_helm_diff(log, current_release, new_release)

    # HACK: workaround for Pydantic to exclude cached properties during model export
    # TODO(Ivan Yordanov): Currently hacky and potentially unsafe. Find cleaner solution
    @model_serializer(mode="wrap", when_used="always")
    def serialize_model(
        self,
        default_serialize_handler: pydantic.SerializerFunctionWrapHandler,
        info: pydantic.SerializationInfo,
    ) -> dict[str, Any]:
        return exclude_by_name(default_serialize_handler(self), "helm", "helm_diff")
