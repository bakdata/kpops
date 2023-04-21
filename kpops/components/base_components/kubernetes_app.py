from __future__ import annotations

import logging
import re
from functools import cached_property
from typing import Any, Literal

from pydantic import BaseModel, Extra, Field
from typing_extensions import override

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmTemplateFlags,
    HelmUpgradeInstallFlags,
)
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.colorify import magentaify
from kpops.utils.docstring import describe_attr, describe_object
from kpops.utils.pydantic import CamelCaseConfig, DescConfig

log = logging.getLogger("KubernetesAppComponent")

KUBERNETES_NAME_CHECK_PATTERN = re.compile(
    r"^(?![0-9]+$)(?!.*-$)(?!-)[a-z0-9-.]{1,253}(?<!_)$"
)


class KubernetesAppConfig(BaseModel):
    """Settings specific to Kubernetes Apps"""

    class Config(CamelCaseConfig, DescConfig):
        extra = Extra.allow


# TODO: label and annotations
class KubernetesApp(PipelineComponent):
    """Base class for all Kubernetes apps.

    All built-in components are Kubernetes apps, except for the Kafka connectors.

    :param type: Component type, defaults to "kubernetes-app"
    :type type: str, optional
    :param schema_type: Used for schema generation, same as :param:`type`,
        defaults to "kubernetes-app"
    :type schema_type: Literal["kubernetes-app"], optional
    :param app: Application-specific settings
    :type app: KubernetesAppConfig
    :param repo_config: Configuration of the Helm chart repo to be used for
        deploying the component, defaults to None
    :type repo_config: HelmRepoConfig, None, optional
    :param namespace: Namespace in which the component shall be deployed
    :type namespace: str
    :param version: Helm chart version, defaults to None
    :type version: str, None, optional
    """

    type: str = Field(
        default="kubernetes-app",
        description=describe_attr("type", __doc__),
    )
    schema_type: Literal["kubernetes-app"] = Field(  # type: ignore[assignment]
        default="kubernetes-app",
        title="Component type",
        description=describe_object(__doc__),
        exclude=True,
    )
    app: KubernetesAppConfig = Field(
        default=...,
        description=describe_attr("app", __doc__),
    )
    repo_config: HelmRepoConfig | None = Field(
        default=None,
        description=describe_attr("repo_config", __doc__),
    )
    namespace: str = Field(
        default=...,
        description=describe_attr("namespace", __doc__),
    )
    version: str | None = Field(
        default=None,
        description=describe_attr("version", __doc__),
    )

    class Config(CamelCaseConfig, DescConfig):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__check_compatible_name()

    @cached_property
    def helm(self) -> Helm:
        """Helm object that contains component-specific config such as repo"""
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
        """Helm diff object of last and current release of this component"""
        return HelmDiff(self.config.helm_diff_config)

    @property
    def helm_release_name(self) -> str:
        """The name for the Helm release. Can be overridden."""
        return self.name

    @override
    def template(
        self, api_version: str | None, ca_file: str | None, cert_file: str | None
    ) -> None:
        flags = HelmTemplateFlags(api_version, ca_file, cert_file, self.version)
        stdout = self.helm.template(
            self.helm_release_name, self.get_helm_chart(), self.to_helm_values(), flags
        )
        print(stdout)

    @override
    def deploy(self, dry_run: bool) -> None:
        stdout = self.helm.upgrade_install(
            self.helm_release_name,
            self.get_helm_chart(),
            dry_run,
            self.namespace,
            self.to_helm_values(),
            HelmUpgradeInstallFlags(
                create_namespace=self.config.create_namespace, version=self.version
            ),
        )
        if dry_run and self.helm_diff.config.enable:
            self.print_helm_diff(stdout)

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
        """Generate a dictionary of values readable by Helm from `self.app`

        :returns: Thte values to be used by Helm
        :rtype: dict
        """
        return self.app.dict(by_alias=True, exclude_none=True, exclude_unset=True)

    def print_helm_diff(self, stdout: str) -> None:
        """Print the diff of the last and current release of this component

        :param stdout: The output of a Helm command that installs or upgrades the release
        :type stdout: str
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

    def get_helm_chart(self) -> str:
        """Return component's helm chart

        :return: Helm chart of this component
        :rtype: str
        """
        raise NotImplementedError(
            f"Please implement the get_helm_chart() method of the {self.__module__} module."
        )

    def __check_compatible_name(self) -> None:
        """Check if the component's name `self.name` is valid for Kubernetes"""
        if not bool(KUBERNETES_NAME_CHECK_PATTERN.match(self.name)):  # TODO: SMARTER
            raise ValueError(
                f"The component name {self.name} is invalid for Kubernetes."
            )

    @override
    def dict(self, *, exclude=None, **kwargs) -> dict[str, Any]:
        # HACK: workaround for Pydantic to exclude cached properties during model export
        if exclude is None:
            exclude = set()
        exclude.add("helm")
        exclude.add("helm_diff")
        return super().dict(exclude=exclude, **kwargs)
