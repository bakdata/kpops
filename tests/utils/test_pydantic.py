from typing import Any

import pytest

from kpops.components.common.kubernetes_model import SerializeAsOptional
from kpops.utils.pydantic import (
    SerializeAsOptionalModel,
    exclude_by_value,
    to_dash,
    to_dot,
    to_snake,
    to_str,
)


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


@pytest.mark.parametrize(
    ("dumped_model", "excluded_values", "expected"),
    [
        pytest.param(
            {},
            (),
            {},
        ),
        pytest.param(
            {},
            (None,),
            {},
        ),
        pytest.param(
            {"foo": 0, "bar": 1},
            (),
            {"foo": 0, "bar": 1},
        ),
        pytest.param(
            {"foo": 0, "bar": 1},
            (None,),
            {"foo": 0, "bar": 1},
        ),
        pytest.param(
            {"foo": 0, "bar": 1},
            (0,),
            {"bar": 1},
        ),
        pytest.param(
            {"foo": 0, "bar": 1},
            (1,),
            {"foo": 0},
        ),
        pytest.param(
            {"foo": None},
            (None,),
            {},
        ),
        pytest.param(
            {"foo": None, "bar": 0},
            (None,),
            {"bar": 0},
        ),
        pytest.param(
            {"foo": None, "bar": 0},
            (None, 0),
            {},
        ),
    ],
)
def test_exclude_by_value(
    dumped_model: dict[str, Any],
    excluded_values: tuple[Any, ...],
    expected: dict[str, Any],
):
    assert exclude_by_value(dumped_model, *excluded_values) == expected


def test_serialize_as_optional():
    class Model(SerializeAsOptionalModel):
        optional_list: SerializeAsOptional[list[str]] = []
        optional_dict: SerializeAsOptional[dict[str, str]] = {}

    model = Model()
    assert model.optional_list == []
    assert model.optional_dict == {}
    assert model.model_dump() == {"optional_list": None, "optional_dict": None}
    assert model.model_dump(exclude_defaults=True) == {}
    assert model.model_dump(exclude_unset=True) == {}
    # this would fail without inheriting from SerializeAsOptionalModel
    assert model.model_dump(exclude_none=True) == {}

    model = Model.model_validate({"optional_list": None, "optional_dict": None})
    assert model.optional_list == []
    assert model.optional_dict == {}

    model = Model(optional_list=["el"], optional_dict={"foo": "bar"})
    assert model.optional_list == ["el"]
    assert model.optional_dict == {"foo": "bar"}
    assert model.model_dump() == {
        "optional_list": ["el"],
        "optional_dict": {"foo": "bar"},
    }
    assert model.model_dump(exclude_defaults=True) == {
        "optional_list": ["el"],
        "optional_dict": {"foo": "bar"},
    }
    assert model.model_dump(exclude_unset=True) == {
        "optional_list": ["el"],
        "optional_dict": {"foo": "bar"},
    }
    assert model.model_dump(exclude_none=True) == {
        "optional_list": ["el"],
        "optional_dict": {"foo": "bar"},
    }
