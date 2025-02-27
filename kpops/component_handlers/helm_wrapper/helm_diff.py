import logging
from collections.abc import Iterable, Iterator
from typing import final

from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate
from kpops.manifests.kubernetes import KubernetesManifest
from kpops.utils.dict_differ import Change, render_diff

log = logging.getLogger("HelmDiff")


@final
class HelmDiff:
    def __init__(self, config: HelmDiffConfig) -> None:
        self.config: HelmDiffConfig = config

    @staticmethod
    def calculate_changes(
        current_release: Iterable[HelmTemplate],
        new_release: Iterable[HelmTemplate],
    ) -> Iterator[Change[KubernetesManifest | None, KubernetesManifest | None]]:
        """Compare 2 releases and generate a Change object for each difference.

        :param current_release: Iterable containing HelmTemplate objects for the current release
        :param new_release: Iterable containing HelmTemplate objects for the new release
        :return: A Generator of Change objects for each difference between the two releases
        """
        new_release_index = {
            helm_template.filepath: helm_template for helm_template in new_release
        }

        # collect changed & deleted files
        for current_resource in current_release:
            # get corresponding dry-run release
            new_resource = new_release_index.pop(current_resource.filepath, None)
            yield Change(
                current_resource.manifest,
                new_resource.manifest if new_resource else None,
            )

        # collect added files
        for new_resource in new_release_index.values():
            yield Change(
                None,
                new_resource.manifest,
            )

    def log_helm_diff(
        self,
        logger: logging.Logger,
        current_release: Iterable[HelmTemplate],
        new_release: Iterable[HelmTemplate],
    ) -> None:
        for change in self.calculate_changes(current_release, new_release):
            if diff := render_diff(
                change.old_value.model_dump() if change.old_value else {},
                change.new_value.model_dump() if change.new_value else {},
                ignore=self.config.ignore,
            ):
                logger.info("\n" + diff)
