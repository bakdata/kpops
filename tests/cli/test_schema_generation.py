from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import pytest
from pydantic import ConfigDict, Field
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.docstring import describe_attr
from kpops.utils.gen_schema import COMPONENTS

RESOURCE_PATH = Path(__file__).parent / "resources"


runner = CliRunner()


# type is inherited from PipelineComponent
class EmptyPipelineComponent(PipelineComponent):
    model_config: ClassVar[ConfigDict] = ConfigDict(str_strip_whitespace=True)


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

    example_attr: str = Field(description=describe_attr("example_attr", __doc__))


@pytest.mark.filterwarnings(
    "ignore:handlers", "ignore:config", "ignore:enrich", "ignore:validate"
)
class TestGenSchema:
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

    def test_gen_defaults_schema(self):
        result = runner.invoke(
            app,
            [
                "schema",
                "defaults",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout
        assert result.stdout
        schema = json.loads(result.stdout)
        assert schema["title"] == "DefaultsSchema"
        assert schema["required"] == [component.type for component in COMPONENTS]

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
