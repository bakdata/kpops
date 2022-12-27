import logging
from typing import Iterable

from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate
from kpops.utils.dict_differ import Change, render_diff

log = logging.getLogger("HelmDiff")


class HelmDiff:
    def __init__(self, config: HelmDiffConfig):
        self.config = config

    @staticmethod
    def get_diff(
        current_release: Iterable[HelmTemplate],
        new_release: Iterable[HelmTemplate],
    ) -> list[Change]:
        new_release_index = {
            helm_template.filepath: helm_template for helm_template in new_release
        }

        changes: list[Change] = []
        # collect changed & deleted files
        for current_resource in current_release:
            # get corresponding dry-run release
            new_resource = new_release_index.pop(current_resource.filepath, None)
            if new_resource:
                change = Change(
                    old_value=current_resource.template, new_value=new_resource.template
                )
            else:
                change = Change(old_value=current_resource.template, new_value={})
            changes.append(change)

        # collect added files
        for new_resource in new_release_index.values():
            changes.append(Change(old_value={}, new_value=new_resource.template))

        return changes

    def log_helm_diff(self, changes: list[Change], logger: logging.Logger):
        for change in changes:
            if change.old_value and change.new_value:
                if diff := render_diff(
                    change.old_value,
                    change.new_value,
                    ignore=self.config.ignore,
                ):
                    logger.info("\n" + diff)
