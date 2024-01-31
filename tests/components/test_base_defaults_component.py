from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pydantic
import pytest

from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
    get_defaults_file_paths,
)
from kpops.config import KpopsConfig
from kpops.pipeline import PIPELINE_PATH
from kpops.utils.environment import ENV

PIPELINE_BASE_DIR = Path(__file__).parent
RESOURCES_PATH = PIPELINE_BASE_DIR / "resources"


class Parent(BaseDefaultsComponent):
    __test__ = False
    name: str | None = None
    value: float | None = None
    hard_coded: str = "hard_coded_value"


class Nested(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="allow")


class Child(Parent):
    __test__ = False
    nice: dict | None = None
    another_hard_coded: str = "another_hard_coded_value"
    nested: Nested | None = None


class GrandChild(Child):
    __test__ = False
    grand_child: str | None = None


class EnvVarTest(BaseDefaultsComponent):
    __test__ = False
    name: str | None = None


@pytest.fixture()
def config() -> KpopsConfig:
    ENV[PIPELINE_PATH] = str(RESOURCES_PATH / "pipelines/pipeline-1/pipeline.yaml")
    config = KpopsConfig()
    config.pipeline_base_dir = PIPELINE_BASE_DIR
    return config


@pytest.fixture()
def handlers() -> ComponentHandlers:
    return ComponentHandlers(
        schema_handler=MagicMock(),
        connector_handler=MagicMock(),
        topic_handler=MagicMock(),
    )


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
        self, component_class: type[BaseDefaultsComponent], defaults: dict
    ):
        assert (
            component_class.load_defaults(RESOURCES_PATH / "defaults.yaml") == defaults
        )

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
        self, component_class: type[BaseDefaultsComponent], defaults: dict
    ):
        assert (
            component_class.load_defaults(
                RESOURCES_PATH / "defaults_development.yaml",
                RESOURCES_PATH / "defaults.yaml",
            )
            == defaults
        )

    def test_inherit_defaults(self, config: KpopsConfig, handlers: ComponentHandlers):
        ENV["environment"] = "development"
        component = Child(config=config, handlers=handlers)

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

    def test_inherit(self, config: KpopsConfig, handlers: ComponentHandlers):
        component = Child(
            config=config,
            handlers=handlers,
            name="name-defined-in-pipeline_parser",
        )

        assert (
            component.name == "name-defined-in-pipeline_parser"
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

    def test_multiple_generations(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ):
        component = GrandChild(config=config, handlers=handlers)

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

    def test_env_var_substitution(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ):
        ENV["pipeline_name"] = str(RESOURCES_PATH)
        component = EnvVarTest(config=config, handlers=handlers)

        assert component.name == str(
            RESOURCES_PATH
        ), "Environment variables should be substituted"

    def test_merge_defaults(self, config: KpopsConfig, handlers: ComponentHandlers):
        component = GrandChild(
            config=config, handlers=handlers, nested=Nested(**{"bar": False})
        )
        assert isinstance(component.nested, Nested)
        assert component.nested == Nested(**{"foo": "foo", "bar": False})

    @pytest.mark.parametrize(
        ("pipeline_path", "environment", "expected_default_paths"),
        [
            (
                RESOURCES_PATH / "pipelines/pipeline-1/pipeline.yaml",
                "development",
                [
                    Path(f"{RESOURCES_PATH}/pipelines/pipeline-1/defaults.yaml"),
                    Path(f"{RESOURCES_PATH}/defaults_development.yaml"),
                    Path(f"{RESOURCES_PATH}/defaults.yaml"),
                ],
            ),
            (
                RESOURCES_PATH / "pipelines/pipeline-3/pipeline-deep/pipeline.yaml",
                "development",
                [
                    Path(
                        f"{RESOURCES_PATH}/pipelines/pipeline-3/pipeline-deep/defaults.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/pipeline-3/defaults_development.yaml"
                    ),
                    Path(f"{RESOURCES_PATH}/pipelines/pipeline-3/defaults.yaml"),
                    Path(f"{RESOURCES_PATH}/defaults_development.yaml"),
                    Path(f"{RESOURCES_PATH}/defaults.yaml"),
                ],
            ),
            (
                RESOURCES_PATH / "pipelines/pipeline-3/pipeline-deep/pipeline.yaml",
                "production",
                [
                    Path(
                        f"{RESOURCES_PATH}/pipelines/pipeline-3/pipeline-deep/defaults_production.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/pipeline-3/pipeline-deep/defaults.yaml"
                    ),
                    Path(
                        f"{RESOURCES_PATH}/pipelines/pipeline-3/defaults_production.yaml"
                    ),
                    Path(f"{RESOURCES_PATH}/pipelines/pipeline-3/defaults.yaml"),
                    Path(f"{RESOURCES_PATH}/defaults.yaml"),
                ],
            ),
        ],
    )
    def test_get_defaults_file_paths(
        self,
        pipeline_path: Path,
        environment: str,
        expected_default_paths: list[Path],
    ):
        config = KpopsConfig()
        config.pipeline_base_dir = PIPELINE_BASE_DIR
        actual_default_paths = get_defaults_file_paths(
            pipeline_path,
            config,
            environment,
        )
        assert len(actual_default_paths) == len(expected_default_paths)
        assert actual_default_paths == expected_default_paths
