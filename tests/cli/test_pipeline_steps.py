from dataclasses import dataclass
from typing import ClassVar, cast
from unittest.mock import patch

from kpops.cli.main import get_steps_to_apply
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
    filtered_steps = get_steps_to_apply(pipeline, steps="example2,example3")

    assert len(filtered_steps) == 2
    assert test_component_2 in filtered_steps
    assert test_component_3 in filtered_steps

    assert log_info.call_count == 2
    log_info.assert_any_call("KPOPS_PIPELINE_STEPS is defined.")
    log_info.assert_any_call(
        "Executing only on the following steps: ['example2', 'example3'], \n ignoring ['example1']"
    )

    filtered_steps = get_steps_to_apply(pipeline, steps=None)
    assert len(filtered_steps) == 3

    filtered_steps = get_steps_to_apply(pipeline, steps="")
    assert len(filtered_steps) == 3
