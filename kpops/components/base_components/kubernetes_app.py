import logging
import re
from functools import cached_property

from pydantic import BaseModel

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.pydantic import CamelCaseConfig

log = logging.getLogger("KubernetesAppComponent")

KUBERNETES_NAME_CHECK_PATTERN = re.compile(
    r"^(?![0-9]+$)(?!.*-$)(?!-)[a-z0-9-.]{1,253}(?<!_)$"
)


class KubernetesAppConfig(BaseModel):
    namespace: str

    class Config(CamelCaseConfig):
        pass


# TODO: label and annotations
class KubernetesApp(PipelineComponent):
    """Base kubernetes app"""

    _type = "kubernetes-app"
    app: KubernetesAppConfig

    version: str | None = None

    class Config:
        keep_untouched = (cached_property,)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__check_compatible_name()

    @cached_property
    def helm(self) -> Helm:
        helm = Helm(self.config.helm_config)
        if self.helm_repo_config is not None:
            helm.add_repo(
                self.helm_repo_config.repository_name,
                self.helm_repo_config.url,
                self.helm_repo_config.repo_auth_flags,
            )
        return helm

    @cached_property
    def helm_diff(self) -> HelmDiff:
        return HelmDiff(self.config.helm_diff_config)

    @property
    def helm_release_name(self) -> str:
        """The name for the Helm release. Can be overridden."""
        return self.name

    @property
    def namespace(self) -> str:
        return self.app.namespace

    @property
    def helm_repo_config(self) -> HelmRepoConfig | None:
        return None

    def deploy(self, dry_run: bool) -> None:
        stdout = self.helm.upgrade_install(
            self.helm_release_name,
            self.get_helm_chart(),
            dry_run,
            self.namespace,
            self.to_helm_values(),
            HelmUpgradeInstallFlags(version=self.version),
        )
        if dry_run and self.helm_diff.config.enable:
            self.print_helm_diff(stdout)

    # TODO: Separate destroy and clean
    def destroy(self, dry_run: bool, clean: bool, delete_outputs: bool) -> None:
        stdout = self.helm.uninstall(
            self.namespace,
            self.helm_release_name,
            dry_run,
        )
        if dry_run and self.helm_diff.config.enable and stdout:
            self.print_helm_diff(stdout)

    def to_helm_values(self) -> dict:
        return self.app.dict(by_alias=True, exclude_none=True, exclude_unset=True)

    def print_helm_diff(self, stdout: str):
        current_release = self.helm.get_manifest(self.helm_release_name, self.namespace)
        new_release = Helm.load_helm_manifest(stdout)
        helm_diff = HelmDiff.get_diff(current_release, new_release)
        self.helm_diff.log_helm_diff(helm_diff, log)

    def get_helm_chart(self) -> str:
        raise NotImplementedError(
            f"Please implement the get_helm_chart() method of the {self.__module__} module."
        )

    def __check_compatible_name(self) -> None:
        if not bool(KUBERNETES_NAME_CHECK_PATTERN.match(self.name)):  # TODO: SMARTER
            raise ValueError(
                f"The component name {self.name} is invalid for Kubernetes."
            )
