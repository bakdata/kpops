from typing import Any

import pytest
from pydantic import BaseModel

from kpops.components.common.kubernetes_model import SerializeAsOptional
from kpops.utils.pydantic import to_dash, to_dot, to_snake, to_str


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("BaseDefaultsComponent", "base-defaults-component"),
        ("ACRONYM", "acronym"),
        ("ACRONYMComponent", "acronym-component"),
        ("ExampleACRONYMComponent", "example-acronym-component"),
        ("ComponentWithACRONYM", "component-with-acronym"),
        ("ComponentWithDIGIT00", "component-with-digit00"),
        ("S3Test", "s3-test"),
    ],
)
def test_to_dash(input: str, expected: str):
    assert to_dash(input) == expected


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("BaseDefaultsComponent", "base_defaults_component"),
        ("ACRONYM", "acronym"),
        ("ACRONYMComponent", "acronym_component"),
        ("ExampleACRONYMComponent", "example_acronym_component"),
        ("ComponentWithACRONYM", "component_with_acronym"),
        ("ComponentWithDIGIT00", "component_with_digit00"),
        ("S3Test", "s3_test"),  # NOTE: this one fails with Pydantic's to_snake util
    ],
)
def test_to_snake(input: str, expected: str):
    assert to_snake(input) == expected


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("connector_class", "connector.class"),
        ("topics_regex", "topics.regex"),
        ("topics", "topics"),
        ("errors_deadletterqueue_topic_name", "errors.deadletterqueue.topic.name"),
    ],
)
def test_to_dot(input: str, expected: str):
    assert to_dot(input) == expected


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("foo", "foo"),
        ("1", "1"),
        (1, "1"),
        (-1, "-1"),
        (1.9, "1.9"),
        (True, "true"),
        (False, "false"),
    ],
)
def test_to_str(input: Any, expected: str):
    assert to_str(input) == expected


def test_serialize_as_optional():
    class Model(BaseModel):
        foo: SerializeAsOptional[list[str]] = []

    model = Model()
    assert model.model_dump() == {"foo": None}
    assert model.model_dump(exclude_defaults=True) == {}
    assert model.model_dump(exclude_unset=True) == {}
    assert model.model_dump(exclude_none=True) == {}
