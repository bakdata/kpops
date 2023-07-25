from dataclasses import dataclass
from typing import cast
from unittest.mock import patch

from kpops.cli.main import FilterType, get_steps_to_apply
from kpops.pipeline_generator.pipeline import Pipeline

PREFIX = "example-prefix-"


@patch("kpops.cli.main.log.info")
def tests_filter_steps_to_apply(log_info):
    @dataclass
    class TestComponent:
        name: str
        prefix: str = PREFIX

    test_component_1 = TestComponent(PREFIX + "example1")
    test_component_2 = TestComponent(PREFIX + "example2")
    test_component_3 = TestComponent(PREFIX + "example3")

    class TestPipeline:
        components = [
            test_component_1,
            test_component_2,
            test_component_3,
        ]

        def __iter__(self):
            return iter(self.components)

    pipeline = cast(Pipeline, TestPipeline())
    filtered_steps = get_steps_to_apply(
        pipeline, "example2,example3", FilterType.include
    )

    assert len(filtered_steps) == 2
    assert test_component_2 in filtered_steps
    assert test_component_3 in filtered_steps

    assert log_info.call_count == 2
    log_info.assert_any_call("KPOPS_PIPELINE_STEPS is defined.")
    log_info.assert_any_call("Including the following steps: ['example2', 'example3']")

    filtered_steps = get_steps_to_apply(pipeline, None, FilterType.include)
    assert len(filtered_steps) == 3

    filtered_steps = get_steps_to_apply(pipeline, "", FilterType.include)
    assert len(filtered_steps) == 3


@patch("kpops.cli.main.log.info")
def tests_filter_steps_to_exclude(log_info):
    @dataclass
    class TestComponent:
        name: str
        prefix: str = PREFIX

    test_component_1 = TestComponent(PREFIX + "example1")
    test_component_2 = TestComponent(PREFIX + "example2")
    test_component_3 = TestComponent(PREFIX + "example3")

    class TestPipeline:
        components = [
            test_component_1,
            test_component_2,
            test_component_3,
        ]

        def __iter__(self):
            return iter(self.components)

    pipeline = cast(Pipeline, TestPipeline())
    filtered_steps = get_steps_to_apply(
        pipeline, "example2,example3", FilterType.exclude
    )

    assert len(filtered_steps) == 1
    assert test_component_1 in filtered_steps

    assert log_info.call_count == 2
    log_info.assert_any_call("KPOPS_PIPELINE_STEPS is defined.")
    log_info.assert_any_call("Excluding the following steps: ['example1']")

    filtered_steps = get_steps_to_apply(pipeline, None, FilterType.exclude)
    assert len(filtered_steps) == 3

    filtered_steps = get_steps_to_apply(pipeline, "", FilterType.exclude)
    assert len(filtered_steps) == 3
