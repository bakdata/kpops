from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

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


class TestPipeline:
    @pytest.fixture(autouse=True)
    def pipeline(self) -> Pipeline:
        pipeline = Pipeline()
        pipeline.add(cast(PipelineComponent, test_component_1))
        pipeline.add(cast(PipelineComponent, test_component_2))
        pipeline.add(cast(PipelineComponent, test_component_3))
        return pipeline

    @pytest.fixture(autouse=True)
    def log_info(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.pipeline.log.info")

    def test_filter_include(self, log_info: MagicMock, pipeline: Pipeline):
        pipeline.filter({"example2", "example3"}, FilterType.INCLUDE)
        assert len(pipeline.components) == 2
        assert test_component_2 in pipeline.components
        assert test_component_3 in pipeline.components
        assert log_info.call_count == 1
        log_info.assert_any_call("Filtered pipeline:\n['example2', 'example3']")

    def test_filter_include_empty(self, pipeline: Pipeline):
        pipeline.filter(set(), FilterType.INCLUDE)
        assert len(pipeline.components) == 0

    def test_filter_exclude(self, log_info: MagicMock, pipeline: Pipeline):
        pipeline.filter({"example2", "example3"}, FilterType.EXCLUDE)
        assert len(pipeline.components) == 1
        assert test_component_1 in pipeline.components

        assert log_info.call_count == 1
        log_info.assert_any_call("Filtered pipeline:\n['example1']")

    def test_filter_exclude_empty(self, pipeline: Pipeline):
        pipeline.filter(set(), FilterType.EXCLUDE)
        assert len(pipeline.components) == 3
