from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pydantic
import pytest

from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.base_defaults_component import (
    BaseDefaultsComponent,
)
from kpops.config import KpopsConfig
from kpops.utils.environment import ENV

DEFAULTS_PATH = Path(__file__).parent / "resources"


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
    return KpopsConfig(defaults_path=DEFAULTS_PATH)


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
            component_class.load_defaults(DEFAULTS_PATH / "defaults.yaml") == defaults
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
                DEFAULTS_PATH / "defaults.yaml",
                DEFAULTS_PATH / "defaults_development.yaml",
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
        ENV["pipeline_name"] = DEFAULTS_PATH.as_posix()
        component = EnvVarTest(config=config, handlers=handlers)

        assert (
            Path(component.name) == DEFAULTS_PATH  # type: ignore[reportAttributeAccessIssue]
        ), "Environment variables should be substituted"

    def test_merge_defaults(self, config: KpopsConfig, handlers: ComponentHandlers):
        component = GrandChild(
            config=config, handlers=handlers, nested=Nested(**{"bar": False})
        )
        assert isinstance(component.nested, Nested)
        assert component.nested == Nested(**{"foo": "foo", "bar": False})
