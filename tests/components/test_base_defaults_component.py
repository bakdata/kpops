import os
from pathlib import Path

import pytest

from kpops.cli import pipeline_config
from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
    update_nested_pair,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestParentModel(BaseDefaultsComponent):
    __test__ = False
    _type: str = "parent"
    name: str | None = None
    value: float | None = None
    hard_coded: str = "hard_coded_value"


class TestChildModel(TestParentModel):
    __test__ = False
    _type: str = "child"
    nice: dict | None = None
    another_hard_coded: str = "another_hard_coded_value"


class TestGrandChildModel(TestChildModel):
    __test__ = False
    _type: str = "grand-child"
    grand_child: str | None = None


class TestBaseDefaultsComponent:
    def test_inherit_defaults(self):
        component = TestChildModel(
            config=pipeline_config.PipelineConfig(
                defaults_path=DEFAULTS_PATH,
                environment="development",
            )
        )

        assert (
            component.name == "fake-child-name"
        ), "Child default should overwrite parent default"
        assert component.nice == {
            "fake-value": "fake"
        }, "Field introduce by child should be added"
        assert (
            component.value == 2.0
        ), "Environment tmp_defaults should always overwrite"
        assert (
            component.another_hard_coded == "another_hard_coded_value"
        ), "Defaults in code should be kept for childs"
        assert (
            component.hard_coded == "hard_coded_value"
        ), "Defaults in code should be kept for parents"

    def test_inherit(self):
        component = TestChildModel(
            config=pipeline_config.PipelineConfig(
                defaults_path=DEFAULTS_PATH,
                environment="development",
            ),
            **{"name": "name-defined-in-pipeline_generator"}
        )

        assert (
            component.name == "name-defined-in-pipeline_generator"
        ), "Kwargs should should overwrite all other values"
        assert component.nice == {
            "fake-value": "fake"
        }, "Field introduce by child should be added"
        assert (
            component.value == 2.0
        ), "Environment tmp_defaults should always overwrite"
        assert (
            component.another_hard_coded == "another_hard_coded_value"
        ), "Defaults in code should be kept for childs"
        assert (
            component.hard_coded == "hard_coded_value"
        ), "Defaults in code should be kept for parents"

    def test_multiple_generations(self):
        component = TestGrandChildModel(
            config=pipeline_config.PipelineConfig(
                defaults_path=DEFAULTS_PATH,
                environment="development",
            )
        )

        assert (
            component.name == "fake-child-name"
        ), "Child default should overwrite parent default"
        assert component.nice == {
            "fake-value": "fake"
        }, "Field introduce by child should be added"
        assert (
            component.value == 2.0
        ), "Environment tmp_defaults should always overwrite"
        assert (
            component.another_hard_coded == "another_hard_coded_value"
        ), "Defaults in code should be kept for childs"
        assert (
            component.hard_coded == "hard_coded_value"
        ), "Defaults in code should be kept for parents"
        assert component.grand_child == "grand-child-value"

    def test_env_var_substitution(self):
        class TestEnvVarModel(BaseDefaultsComponent):
            _type: str = "env-var-test"
            name: str | None = None

        os.environ["pipeline_name"] = str(DEFAULTS_PATH)
        component = TestEnvVarModel(
            config=pipeline_config.PipelineConfig(
                defaults_path=DEFAULTS_PATH,
                environment="development",
            )
        )

        assert component.name == str(
            DEFAULTS_PATH
        ), "Environment variables should be substituted"

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
