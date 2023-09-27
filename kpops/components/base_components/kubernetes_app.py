from __future__ import annotations

import logging
import re
from functools import cached_property
from typing import Any

from pydantic import BaseModel, Extra, Field
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
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr
from kpops.utils.pydantic import CamelCaseConfig, DescConfig

log = logging.getLogger("KubernetesAppComponent")

KUBERNETES_NAME_CHECK_PATTERN = re.compile(
    r"^(?![0-9]+$)(?!.*-$)(?!-)[a-z0-9-.]{1,253}(?<!_)$"
)


class KubernetesAppConfig(BaseModel):
    """Settings specific to Kubernetes Apps."""

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.allow


class KubernetesApp(PipelineComponent):
    """Base class for all Kubernetes apps.

    All built-in components are Kubernetes apps, except for the Kafka connectors.

    :param app: Application-specific settings
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to None this means that the command "helm repo add" is not called and Helm
        expects a path to local Helm chart.
    :param namespace: Namespace in which the component shall be deployed
    :param version: Helm chart version, defaults to None
    """

    namespace: str = Field(
        default=...,
        description=describe_attr("namespace", __doc__),
    )
    app: KubernetesAppConfig = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    repo_config: HelmRepoConfig | None = Field(
        default=None,
        description=describe_attr("repo_config", __doc__),
    )
    version: str | None = Field(
        default=None,
        description=describe_attr("version", __doc__),
    )

    @cached_property
    def helm(self) -> Helm:
        """Helm object that contains component-specific config such as repo."""
        helm = Helm(self.config.helm_config)
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
        return HelmDiff(self.config.helm_diff_config)

    @cached_property
    def dry_run_handler(self) -> DryRunHandler:
        helm_diff = HelmDiff(self.config.helm_diff_config)
        return DryRunHandler(self.helm, helm_diff, self.namespace)

    @property
    def helm_release_name(self) -> str:
        """The name for the Helm release. Can be overridden."""
        return self.full_name

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
        auth_flags = self.repo_config.repo_auth_flags.dict() if self.repo_config else {}
        return HelmFlags(
            **auth_flags,
            version=self.version,
            create_namespace=self.config.create_namespace,
        )

    @property
    def template_flags(self) -> HelmTemplateFlags:
        """Return flags for Helm template command."""
        return HelmTemplateFlags(
            **self.helm_flags.dict(),
            api_version=self.config.helm_config.api_version,
        )

    @override
    def template(self) -> None:
        stdout = self.helm.template(
            self.helm_release_name,
            self.helm_chart,
            self.namespace,
            self.to_helm_values(),
            self.template_flags,
        )
        print(stdout)

    @property
    def deploy_flags(self) -> HelmUpgradeInstallFlags:
        """Return flags for Helm upgrade install command."""
        return HelmUpgradeInstallFlags(**self.helm_flags.dict())

    @override
    def deploy(self, dry_run: bool) -> None:
        stdout = self.helm.upgrade_install(
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
    def destroy(self, dry_run: bool) -> None:
        stdout = self.helm.uninstall(
            self.namespace,
            self.helm_release_name,
            dry_run,
        )

        if stdout:
            log.info(magentaify(stdout))

    def to_helm_values(self) -> dict:
        """Generate a dictionary of values readable by Helm from `self.app`.

        :returns: Thte values to be used by Helm
        """
        return self.app.dict(by_alias=True, exclude_none=True, exclude_defaults=True)

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

    @override
    def _validate_custom(self, **kwargs) -> None:
        super()._validate_custom(**kwargs)
        self.validate_kubernetes_name(self.name)

    @staticmethod
    def validate_kubernetes_name(name: str) -> None:
        """Check if a name is valid for a Kubernetes resource.

        :param name: Name that is to be used for the resource
        :raises ValueError: The component name {name} is invalid for Kubernetes.
        """
        if not bool(KUBERNETES_NAME_CHECK_PATTERN.match(name)):
            msg = f"The component name {name} is invalid for Kubernetes."
            raise ValueError(msg)

    @override
    def dict(self, *, exclude=None, **kwargs) -> dict[str, Any]:
        # HACK: workaround for Pydantic to exclude cached properties during model export
        if exclude is None:
            exclude = set()
        exclude.add("helm")
        exclude.add("helm_diff")
        return super().dict(exclude=exclude, **kwargs)
