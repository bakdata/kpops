import logging
from typing import Iterable

from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate
from kpops.utils.dict_differ import render_diff

log = logging.getLogger("HelmDiff")


class HelmDiff:
    def __init__(self, config: HelmDiffConfig):
        self.config = config

    def get_diff(
        self,
        current_release: Iterable[HelmTemplate],
        new_release: Iterable[HelmTemplate],
    ) -> list[tuple[dict, dict]]:
        new_release_index = {
            helm_template.filepath: helm_template for helm_template in new_release
        }

        changes: list[tuple[dict, dict]] = []
        # collect changed & deleted files
        for current_resource in current_release:
            # get corresponding dry-run release
            new_resource = new_release_index.pop(current_resource.filepath, None)
            changes.append(
                (
                    current_resource.template,
                    new_resource.template if new_resource else {},
                )
            )

        # collect added files
        for new_resource in new_release_index.values():
            changes.append(({}, new_resource.template))

        for before, after in changes:
            if diff := render_diff(
                before,
                after,
                ignore=self.config.ignore,
            ):
                log.info("\n" + diff)
        return changes
