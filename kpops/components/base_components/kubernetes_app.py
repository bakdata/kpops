import logging
import re

from pydantic import BaseModel, Field

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

    version: str | None = Field(default=None, exclude=True)

    _helm_wrapper: Helm | None = None
    _helm_diff: HelmDiff | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__check_compatible_name()

    @property
    def helm_wrapper(self) -> Helm:
        if self._helm_wrapper is None:
            self._helm_wrapper = Helm(self.config.helm_config)
            helm_repo_config = self.get_helm_repo_config()
            if helm_repo_config is not None:
                self._helm_wrapper.add_repo(
                    helm_repo_config.repository_name,
                    helm_repo_config.url,
                    helm_repo_config.repo_auth_flags,
                )
        return self._helm_wrapper

    @property
    def helm_diff(self) -> HelmDiff:
        if self._helm_diff is None:
            self._helm_diff = HelmDiff(self.config.helm_diff_config)
        return self._helm_diff

    @property
    def helm_release_name(self) -> str:
        """The name for the Helm release. Can be overridden."""
        return self.name

    @property
    def namespace(self) -> str:
        return self.app.namespace

    def deploy(self, dry_run: bool) -> None:
        stdout = self.helm_wrapper.upgrade_install(
            self.helm_release_name,
            self.get_helm_chart(),
            dry_run,
            self.namespace,
            self.to_helm_values(),
            HelmUpgradeInstallFlags(version=self.get_helm_chart_version()),
        )

        if dry_run and self.helm_diff.config.enable:
            self.print_helm_diff(stdout)

    # TODO: Separate destroy and clean
    def destroy(self, dry_run: bool, clean: bool, delete_outputs: bool) -> None:
        stdout = self.helm_wrapper.uninstall(
            self.namespace,
            self.helm_release_name,
            dry_run,
        )
        if dry_run and self.helm_diff.config.enable:
            self.print_helm_diff(stdout)

    def to_helm_values(self) -> dict:
        return self.app.dict(by_alias=True, exclude_none=True, exclude_unset=True)

    def print_helm_diff(self, stdout: str):
        current_release = self.helm_wrapper.get_manifest(
            self.helm_release_name, self.namespace
        )
        new_release = Helm.load_helm_manifest(stdout)
        helm_diff = HelmDiff.get_diff(current_release, new_release)
        self.helm_diff.log_helm_diff(helm_diff, log)

    def get_helm_repo_config(self) -> HelmRepoConfig | None:
        return None

    def get_helm_chart(self) -> str:
        raise NotImplementedError(
            f"Please implement the get_helm_chart() method of the {self.__module__} module."
        )

    def get_helm_chart_version(self) -> str | None:
        return self.version

    def __check_compatible_name(self) -> None:
        if not bool(KUBERNETES_NAME_CHECK_PATTERN.match(self.name)):  # TODO: SMARTER
            raise ValueError(
                f"The component name {self.name} is invalid for Kubernetes."
            )
