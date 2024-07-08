from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kpops.components.base_components.pipeline_component import PipelineComponent
    from kpops.pipeline import ComponentFilterPredicate


class FilterType(str, Enum):
    INCLUDE = "include"
    EXCLUDE = "exclude"

    @staticmethod
    def is_in_steps(component: PipelineComponent, component_names: set[str]) -> bool:
        return component.name in component_names

    def create_default_step_names_filter_predicate(
        self, component_names: set[str]
    ) -> ComponentFilterPredicate:
        def predicate(component: PipelineComponent) -> bool:
            match self, FilterType.is_in_steps(component, component_names):
                case (FilterType.INCLUDE, False) | (FilterType.EXCLUDE, True):
                    return False
                case _:
                    return True

        return predicate
