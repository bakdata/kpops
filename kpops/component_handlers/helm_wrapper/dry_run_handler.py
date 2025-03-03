from logging import Logger
from typing import final

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff


@final
class DryRunHandler:
    def __init__(self, helm: Helm, helm_diff: HelmDiff, namespace: str) -> None:
        self._helm = helm
        self._helm_diff = helm_diff
        self.namespace = namespace

    def print_helm_diff(self, stdout: str, helm_release_name: str, log: Logger) -> None:
        """Print the diff of the last and current release of this component.

        :param stdout: The output of a Helm command that installs or upgrades the release
        :param helm_release_name: The Helm release name
        :param log: The Logger object of the component class
        """
        current_release = list(
            self._helm.get_manifest(helm_release_name, self.namespace)
        )
        if current_release:
            log.info(f"Helm release {helm_release_name} already exists")
        else:
            log.info(f"Helm release {helm_release_name} does not exist")
        new_release = Helm.load_manifest(stdout)
        self._helm_diff.log_helm_diff(log, current_release, new_release)
