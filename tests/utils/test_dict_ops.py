import json

import pytest
from pydantic import BaseModel

from kpops.utils.dict_ops import generate_substitution, update_nested_pair


class TestDictOps:
    @pytest.mark.parametrize(
        ("d1", "d2", "expected"),
        [
            (
                {},
                {},
                {},
            ),
            # deep update nested dicts
            (
                {"k1": {"foo": 1}},
                {"k1": {"bar": ""}},
                {"k1": {"foo": 1, "bar": ""}},
            ),
            # do not overwrite different value types, dict in ``original_dict``
            (
                {"k1": {"bar": ""}},
                {"k1": 1},
                {"k1": {"bar": ""}},
            ),
            # do not overwrite different value types, dict in ``other_dict``
            (
                {"k1": 1},
                {"k1": {"bar": ""}},
                {"k1": 1},
            ),
            # do not overwrite None
            (
                {"k1": None},
                {"k1": {"foo": "bar"}},
                {"k1": None},
            ),
            # do not overwrite existing values
            (
                {"k1": 1},
                {"k1": 2},
                {"k1": 1},
            ),
        ],
    )
    def test_update_nested_pair(self, d1: dict, d2: dict, expected: dict):
        assert update_nested_pair(d1, d2) == expected

    def test_substitution_generation(self):
        class SimpleModel(BaseModel):
            name: str
            type_: str
            field_nested_dict: dict
            problems: int

        model = json.loads(
            SimpleModel(
                name="name",
                type_="type",
                field_nested_dict={
                    "value_is_none": None,
                    "value_is_str": "str",
                    "value_is_int": 0,
                    "value_is_dict": {
                        "nested_key": "nested_value",
                    },
                },
                problems=99,
            ).model_dump_json()
        )
        existing_substitution = {
            "key1": "Everything",
            "key2": "work",
            "key3": "well",
            "first_half": "${key1}_seems_to_${key2}",
            "key": "${first_half}_${key3}",
            "name": "pre-existing-name",
        }
        substitution = generate_substitution(model, "prefix", existing_substitution)
        assert substitution == {
            "first_half": "${key1}_seems_to_${key2}",
            "key": "${first_half}_${key3}",
            "key1": "Everything",
            "key2": "work",
            "key3": "well",
            "name": "pre-existing-name",
            "prefix_field_nested_dict_value_is_dict_nested_key": "nested_value",
            "prefix_field_nested_dict_value_is_int": 0,
            "prefix_field_nested_dict_value_is_none": None,
            "prefix_field_nested_dict_value_is_str": "str",
            "prefix_name": "name",
            "prefix_problems": 99,
            "prefix_type_": "type",
        }