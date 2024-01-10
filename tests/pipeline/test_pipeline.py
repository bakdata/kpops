from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

import pytest

from kpops.cli.options import FilterType
from kpops.components import PipelineComponent
from kpops.pipeline import Pipeline

PREFIX = "example-prefix-"


@dataclass
class TestComponent:
    __test__ = False
    name: str
    prefix: str = PREFIX


test_component_1 = TestComponent("example1")
test_component_2 = TestComponent("example2")
test_component_3 = TestComponent("example3")


def is_in_steps(component: PipelineComponent, component_names: set[str]) -> bool:
    return component.name in component_names


def predicate(component_names: set[str]) -> Callable[[PipelineComponent], bool]:
    def inner(component: PipelineComponent) -> bool:
        return is_in_steps(component, component_names)

    return inner


class TestPipeline:
    @pytest.fixture(autouse=True)
    def pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        pipeline.add(cast(PipelineComponent, test_component_1))
        pipeline.add(cast(PipelineComponent, test_component_2))
        pipeline.add(cast(PipelineComponent, test_component_3))
        return pipeline

    def test_filter_include(self, pipeline: Pipeline):
        pipeline.filter(predicate({"example2", "example3"}), FilterType.INCLUDE)
        assert len(pipeline.components) == 2
        assert test_component_2 in pipeline.components
        assert test_component_3 in pipeline.components

    def test_filter_include_empty(self, pipeline: Pipeline):
        pipeline.filter(predicate(set()), FilterType.INCLUDE)
        assert len(pipeline.components) == 0

    def test_filter_exclude(self, pipeline: Pipeline):
        pipeline.filter(predicate({"example2", "example3"}), FilterType.EXCLUDE)
        assert len(pipeline.components) == 1
        assert test_component_1 in pipeline.components

    def test_filter_exclude_empty(self, pipeline: Pipeline):
        pipeline.filter(predicate(set()), FilterType.EXCLUDE)
        assert len(pipeline.components) == 3
