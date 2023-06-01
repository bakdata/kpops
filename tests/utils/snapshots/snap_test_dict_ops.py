# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestDictOps.test_substitution_generation test-substitution"] = {
    "first_half": "${key1}_seems_to_${key2}",
    "key": "${first_half}_${key3}",
    "key1": "Everything",
    "key2": "work",
    "key3": "well",
    "name": "pre-existing-name",
    "prefix_field_nested_dict": {
        "value_is_dict": {"nested_key": "nested_value"},
        "value_is_int": 0,
        "value_is_none": None,
        "value_is_str": "str",
    },
    "prefix_field_nested_dict_value_is_dict": {"nested_key": "nested_value"},
    "prefix_field_nested_dict_value_is_dict_nested_key": "nested_value",
    "prefix_field_nested_dict_value_is_int": 0,
    "prefix_field_nested_dict_value_is_none": None,
    "prefix_field_nested_dict_value_is_str": "str",
    "prefix_name": "name",
    "prefix_type_": "type",
}
