from typing import final

import structlog

from kpops.component_handlers.helm.helm import Helm
from kpops.component_handlers.helm.helm_diff import HelmDiff


@final
class DryRunHandler:
    def __init__(self, helm: Helm, helm_diff: HelmDiff, namespace: str) -> None:
        self._helm = helm
        self._helm_diff = helm_diff
        self.namespace = namespace

    def print_helm_diff(
        self, stdout: str, helm_release_name: str, log: structlog.stdlib.BoundLogger
    ) -> None:
        """Print the diff of the last and current release of this component.

        :param stdout: The output of a Helm command that installs or upgrades the release
        :param helm_release_name: The Helm release name
        :param log: The Logger object of the component class
        """
        current_release = list(
            self._helm.get_manifest(helm_release_name, self.namespace)
        )
        if current_release:
            log.info("Helm release already exists", release=helm_release_name)
        else:
            log.info("Helm release does not exist", release=helm_release_name)
        new_release = Helm.load_manifest(stdout)
        self._helm_diff.log_helm_diff(log, current_release, new_release)
