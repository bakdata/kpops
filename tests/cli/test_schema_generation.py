from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import ConfigDict, Field
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.cli.registry import Registry
from kpops.components import PipelineComponent
from kpops.utils.docstring import describe_attr

if TYPE_CHECKING:
    from pytest_snapshot.plugin import Snapshot

RESOURCE_PATH = Path(__file__).parent / "resources"


runner = CliRunner()


# type is inherited from PipelineComponent
class EmptyPipelineComponent(PipelineComponent):
    model_config = ConfigDict(str_strip_whitespace=True)


# abstract component inheriting from ABC should be excluded
class AbstractBaseComponent(PipelineComponent, ABC): ...


# abstract component with abstractmethods should be excluded
class AbstractPipelineComponent(AbstractBaseComponent):
    @abstractmethod
    def not_implemented(self) -> None: ...


class SubPipelineComponent(EmptyPipelineComponent): ...


# type is inherited from SubPipelineComponent
class SubPipelineComponentNoSchemaTypeNoType(SubPipelineComponent): ...


# Correctly defined
class SubPipelineComponentCorrect(SubPipelineComponent): ...


# Correctly defined, docstr test
class SubPipelineComponentCorrectDocstr(SubPipelineComponent):
    """Newline before title is removed.

    Summarry is correctly imported.
        All
            whitespaces are      removed and replaced with a single space.

    The description extraction terminates at the correct place, deletes 1 trailing coma

    ,

    :param example_attr: Parameter description looks correct and it is not included in
        the class description,
        terminates here ,
        defaults to anything really, this here should not be included as it follows
        a terminating substring and does not follow reST spec.
        if error_marker is found in result.stdout, the description extraction does
        not work correctly.,!?:error_marker   :: "!$%
    :param error_marker: error_marker
    """

    example_attr: str = Field(
        default=..., description=describe_attr("example_attr", __doc__)
    )


@pytest.mark.filterwarnings(
    "ignore:handlers", "ignore:config", "ignore:enrich", "ignore:validate"
)
class TestGenSchema:
    @pytest.fixture
    def stock_components(self) -> list[type[PipelineComponent]]:
        registry = Registry()
        registry.find_components("kpops.components")
        return list(registry._classes.values())

    def test_gen_pipeline_schema_no_modules(self):
        with pytest.raises(
            RuntimeError, match="^No components are provided, no schema is generated.$"
        ):
            runner.invoke(
                app,
                [
                    "schema",
                    "pipeline",
                    "--no-include-stock-components",
                    "--config",
                    str(RESOURCE_PATH / "no_module"),
                ],
                catch_exceptions=False,
            )

    def test_gen_pipeline_schema_no_components(self):
        with pytest.raises(RuntimeError, match="^No valid components found.$"):
            runner.invoke(
                app,
                [
                    "schema",
                    "pipeline",
                    "--no-include-stock-components",
                    "--config",
                    str(RESOURCE_PATH / "empty_module"),
                ],
                catch_exceptions=False,
            )

    def test_gen_pipeline_schema_only_stock_module(self):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout
        assert result.stdout

        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
                "--include-stock-components",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout
        assert result.stdout

    def test_gen_pipeline_schema_only_custom_module(
        self, snapshot: Snapshot, stock_components: list[type[PipelineComponent]]
    ):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
                "--no-include-stock-components",
                "--config",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        snapshot.assert_match(result.stdout, "schema.json")
        schema = json.loads(result.stdout)
        assert schema["title"] == "PipelineSchema"
        assert set(schema["items"]["discriminator"]["mapping"].keys()).isdisjoint(
            {component.type for component in stock_components}
        )

    def test_gen_pipeline_schema_stock_and_custom_module(self):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout
        assert result.stdout

    def test_gen_defaults_schema(self, stock_components: list[type[PipelineComponent]]):
        result = runner.invoke(
            app,
            [
                "schema",
                "defaults",
                "--config",
                str(RESOURCE_PATH / "no_module"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout
        assert result.stdout
        schema = json.loads(result.stdout)
        assert schema["title"] == "DefaultsSchema"
        assert schema["required"] == [component.type for component in stock_components]

    def test_gen_config_schema(self):
        result = runner.invoke(
            app,
            [
                "schema",
                "config",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout
        assert result.stdout
