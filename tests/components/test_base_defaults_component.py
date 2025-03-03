from __future__ import annotations

from pathlib import Path
from typing import Any

import pydantic
import pytest

from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
    get_defaults_file_paths,
)
from kpops.config import KpopsConfig
from kpops.const.file_type import DEFAULTS_YAML, PIPELINE_YAML, KpopsFileType
from kpops.utils.environment import ENV, PIPELINE_PATH
from tests.components import PIPELINE_BASE_DIR, RESOURCES_PATH


class Parent(BaseDefaultsComponent):
    __test__ = False
    name: str | None = None
    value: float | None = None
    hard_coded: str = "hard_coded_value"


class Nested(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")


class Child(Parent):
    __test__ = False
    nice: dict[str, str] | None = None
    another_hard_coded: str = "another_hard_coded_value"
    nested: Nested | None = None


class GrandChild(Child):
    __test__ = False
    grand_child: str | None = None


class EnvVarTest(BaseDefaultsComponent):
    __test__ = False
    name: str | None = None


@pytest.fixture(autouse=True)
def env() -> None:
    ENV[PIPELINE_PATH] = str(RESOURCES_PATH / "pipeline.yaml")


class TestBaseDefaultsComponent:
    @pytest.mark.parametrize(
        ("component_class", "defaults"),
        [
            (BaseDefaultsComponent, {}),
            (
                Parent,
                {
                    "name": "fake-name",
                    "value": 1.0,
                },
            ),
            (
                Child,
                {
                    "name": "fake-child-name",
                    "nice": {"fake-value": "must-be-overwritten"},
                    "value": 1.0,
                    "nested": {"foo": "foo"},
                },
            ),
        ],
    )
    def test_load_defaults(
        self, component_class: type[BaseDefaultsComponent], defaults: dict[str, Any]
    ):
        assert component_class.load_defaults(RESOURCES_PATH / DEFAULTS_YAML) == defaults

    @pytest.mark.parametrize(
        ("component_class", "defaults"),
        [
            (BaseDefaultsComponent, {}),
            (
                Parent,
                {
                    "name": "fake-name",
                    "value": 2.0,
                },
            ),
            (
                Child,
                {
                    "name": "fake-child-name",
                    "nice": {"fake-value": "fake"},
                    "value": 2.0,
                    "nested": {"foo": "foo"},
                },
            ),
        ],
    )
    def test_load_defaults_with_environment(
        self, component_class: type[BaseDefaultsComponent], defaults: dict[str, Any]
    ):
        assert (
            component_class.load_defaults(
                RESOURCES_PATH
                / KpopsFileType.DEFAULTS.as_yaml_file(suffix="_development"),
                RESOURCES_PATH / DEFAULTS_YAML,
            )
            == defaults
        )

    def test_inherit_defaults(self):
        ENV["environment"] = "development"
        component = Child()

        assert component.name == "fake-child-name", (
            "Child default should overwrite parent default"
        )
        assert component.nice == {"fake-value": "fake"}, (
            "Field introduce by child should be added"
        )
        assert component.value == 2.0, (
            "Environment tmp_defaults should always overwrite"
        )
        assert component.another_hard_coded == "another_hard_coded_value", (
            "Defaults in code should be kept for childs"
        )
        assert component.hard_coded == "hard_coded_value", (
            "Defaults in code should be kept for parents"
        )

    def test_inherit(self):
        component = Child(
            name="name-defined-in-pipeline_parser",
        )

        assert component.name == "name-defined-in-pipeline_parser", (
            "Kwargs should should overwrite all other values"
        )
        assert component.nice == {"fake-value": "fake"}, (
            "Field introduce by child should be added"
        )
        assert component.value == 2.0, (
            "Environment tmp_defaults should always overwrite"
        )
        assert component.another_hard_coded == "another_hard_coded_value", (
            "Defaults in code should be kept for childs"
        )
        assert component.hard_coded == "hard_coded_value", (
            "Defaults in code should be kept for parents"
        )

    def test_multiple_generations(self):
        component = GrandChild()

        assert component.name == "fake-child-name", (
            "Child default should overwrite parent default"
        )
        assert component.nice == {"fake-value": "fake"}, (
            "Field introduce by child should be added"
        )
        assert component.value == 2.0, (
            "Environment tmp_defaults should always overwrite"
        )
        assert component.another_hard_coded == "another_hard_coded_value", (
            "Defaults in code should be kept for childs"
        )
        assert component.hard_coded == "hard_coded_value", (
            "Defaults in code should be kept for parents"
        )
        assert component.grand_child == "grand-child-value"

    def test_env_var_substitution(self):
        ENV["pipeline_name"] = RESOURCES_PATH.as_posix()
        component = EnvVarTest()

        assert component.name

        assert Path(component.name) == RESOURCES_PATH, (
            "Environment variables should be substituted"
        )

    def test_merge_defaults(self):
        component = GrandChild(nested=Nested.model_validate({"bar": False}))
        assert isinstance(component.nested, Nested)
        assert component.nested == Nested.model_validate({"foo": "foo", "bar": False})

    @pytest.mark.parametrize(
        ("pipeline_path", "environment", "expected_default_paths"),
        [
            (
                RESOURCES_PATH
                / "pipelines/test-distributed-defaults/pipeline-deep"
                / PIPELINE_YAML,
                None,
                [
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/pipeline-deep"
                    )
                    / DEFAULTS_YAML,
                    Path(f"{RESOURCES_PATH}/pipelines/test-distributed-defaults")
                    / DEFAULTS_YAML,
                    Path(RESOURCES_PATH) / DEFAULTS_YAML,
                ],
            ),
            (
                RESOURCES_PATH
                / "pipelines/test-distributed-defaults/pipeline-deep/pipeline.yaml",
                "development",
                [
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/pipeline-deep/defaults.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/defaults_development.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/defaults.yaml"
                    ),
                    Path(f"{RESOURCES_PATH}/defaults_development.yaml"),
                    Path(f"{RESOURCES_PATH}/defaults.yaml"),
                ],
            ),
            (
                RESOURCES_PATH
                / "pipelines/test-distributed-defaults/pipeline-deep/pipeline.yaml",
                "production",
                [
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/pipeline-deep/defaults_production.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/pipeline-deep/defaults.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/defaults_production.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/test-distributed-defaults/defaults.yaml"
                    ),
                    Path(f"{RESOURCES_PATH}/defaults.yaml"),
                ],
            ),
        ],
    )
    def test_get_defaults_file_paths(
        self,
        pipeline_path: Path,
        environment: str | None,
        expected_default_paths: list[Path],
    ):
        config = KpopsConfig()  # pyright: ignore[reportCallIssue]
        config.pipeline_base_dir = PIPELINE_BASE_DIR
        actual_default_paths = get_defaults_file_paths(
            pipeline_path,
            config,
            environment,
        )
        assert len(actual_default_paths) == len(expected_default_paths)
        assert actual_default_paths == expected_default_paths
