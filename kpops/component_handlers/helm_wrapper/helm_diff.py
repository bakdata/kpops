import logging
from collections.abc import Sequence
from typing import Iterable

from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate
from kpops.utils.dict_differ import Change, render_diff

log = logging.getLogger("HelmDiff")


class HelmDiff:
    def __init__(self, config: HelmDiffConfig) -> None:
        self.config: HelmDiffConfig = config

    @staticmethod
    def get_diff(
        current_release: Iterable[HelmTemplate],
        new_release: Iterable[HelmTemplate],
    ) -> list[Change[dict]]:
        new_release_index = {
            helm_template.filepath: helm_template for helm_template in new_release
        }

        changes: list[Change] = []
        # collect changed & deleted files
        for current_resource in current_release:
            # get corresponding dry-run release
            new_resource = new_release_index.pop(current_resource.filepath, None)
            changes.append(
                Change(
                    current_resource.template,
                    new_resource.template if new_resource else {},
                )
            )

        # collect added files
        for new_resource in new_release_index.values():
            changes.append(Change({}, new_resource.template))

        return changes

    def log_helm_diff(
        self, changes: Sequence[Change[dict]], logger: logging.Logger
    ) -> None:
        for change in changes:
            if diff := render_diff(
                change.old_value,
                change.new_value,
                ignore=self.config.ignore,
            ):
                logger.info("\n" + diff)
