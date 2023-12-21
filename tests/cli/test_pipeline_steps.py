from dataclasses import dataclass
from typing import cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.main import FilterType, get_steps_to_apply
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


@pytest.fixture(autouse=True)
def pipeline() -> Pipeline:
    pipeline = Pipeline()
    pipeline.add(cast(PipelineComponent, test_component_1))
    pipeline.add(cast(PipelineComponent, test_component_2))
    pipeline.add(cast(PipelineComponent, test_component_3))
    return pipeline


@pytest.fixture(autouse=True)
def log_info(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("kpops.cli.main.log.info")


def tests_filter_steps_to_apply(log_info: MagicMock, pipeline: Pipeline):
    filtered_steps = get_steps_to_apply(
        pipeline, "example2,example3", FilterType.INCLUDE
    )

    assert len(filtered_steps) == 2
    assert test_component_2 in filtered_steps
    assert test_component_3 in filtered_steps

    assert log_info.call_count == 1
    log_info.assert_any_call(
        "The following steps are included:\n['example2', 'example3']"
    )

    filtered_steps = get_steps_to_apply(pipeline, None, FilterType.INCLUDE)
    assert len(filtered_steps) == 3

    filtered_steps = get_steps_to_apply(pipeline, "", FilterType.INCLUDE)
    assert len(filtered_steps) == 3


def tests_filter_steps_to_exclude(log_info: MagicMock, pipeline: Pipeline):
    filtered_steps = get_steps_to_apply(
        pipeline, "example2,example3", FilterType.EXCLUDE
    )

    assert len(filtered_steps) == 1
    assert test_component_1 in filtered_steps

    assert log_info.call_count == 1
    log_info.assert_any_call("The following steps are included:\n['example1']")

    filtered_steps = get_steps_to_apply(pipeline, None, FilterType.EXCLUDE)
    assert len(filtered_steps) == 3

    filtered_steps = get_steps_to_apply(pipeline, "", FilterType.EXCLUDE)
    assert len(filtered_steps) == 3
