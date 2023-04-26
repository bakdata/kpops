from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import pytest
from pydantic import Field
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components import PipelineComponent
from kpops.utils.docstring import describe_attr, describe_object

RESOURCE_PATH = Path(__file__).parent / "resources"


runner = CliRunner()


# schema_type and type not defined
class EmptyPipelineComponent(PipelineComponent):
    ...


# schema_type does not exist
class PipelineComponentNoSchemaType(EmptyPipelineComponent):
    type: str = "pipeline-component-no-schema-type"


class SubPipelineComponent(EmptyPipelineComponent):
    type: str = "sub-pipeline-component"
    schema_type: Literal["sub-pipeline-component"] = Field(  # type: ignore[assignment]
        default="sub-pipeline-component", exclude=True
    )


# schema_type is inherited from SubPipelineComponent
class SubPipelineComponentNoSchemaType(SubPipelineComponent):
    type: str = "sub-pipeline-component-no-schema-type"


# schema_type and type are inherited from SubPipelineComponent
class SubPipelineComponentNoSchemaTypeNoType(SubPipelineComponent):
    ...


# schema_type not Literal
class SubPipelineComponentBadSchemaTypeDef(SubPipelineComponent):
    type: str = "sub-pipeline-component-bad-schema-type-def"
    schema_type: str = "sub-pipeline-component-bad-schema-type-def"  # type: ignore [assignment]


# schema_type Literal arg not same as default value
class SubPipelineComponentBadSchemaTypeNoMatchDefault(SubPipelineComponent):
    type: str = "sub-pipeline-component-bad-schema-type-no-match-default"
    schema_type: Literal["sub-pipeline-component-bad-schema-type-no-match-default-NO-MATCH"] = Field(  # type: ignore[assignment]
        default="sub-pipeline-component-bad-schema-type-no-match-default", exclude=True
    )


# schema_type not matching type
class SubPipelineComponentBadSchemaTypeDefNotMatching(SubPipelineComponent):
    type: str = "sub-pipeline-component-not-matching"
    schema_type: Literal["sub-pipeline-component-bad-schema-type-def-not-matching"] = Field(  # type: ignore[assignment]
        default="sub-pipeline-component-bad-schema-type-def-not-matching", exclude=True
    )


# schema_type no default
class SubPipelineComponentBadSchemaTypeMissingDefault(SubPipelineComponent):
    type: str = "sub-pipeline-component-bad-schema-type-default-not-set"
    schema_type: Literal["sub-pipeline-component-bad-schema-type-default-not-set"] = Field(  # type: ignore[assignment]
        exclude=True
    )


# Correctly defined
class SubPipelineComponentCorrect(SubPipelineComponent):
    type: str = "sub-pipeline-component-correct"
    schema_type: Literal["sub-pipeline-component-correct"] = Field(  # type: ignore[assignment]
        default="sub-pipeline-component-correct", exclude=True
    )


# Correctly defined, docstr test
class SubPipelineComponentCorrectDocstr(SubPipelineComponent):
    """
    Newline before title is removed

    Summarry is correctly imported.
        All
            whitespaces are      removed and replaced with a single space.

    The description extraction terminates at the correct place, deletes 1 trailing coma

    ,

    :param type: Parameter description looks correct and it is not included in
        the class description,
        terminates here ,
        defaults to anything really, this here should not be included as it follows
        a terminating substring and does not follow reST spec.
        if error_marker is found in result.stdout, the description extraction does
        not work correctly.,!?:error_marker   :: "!$%
    :type type: This line should not appear anywhere error_marker
    :param schema_type: This description should not be applied to schema_type as
        it instead reads the class description. error_marker
    :type schema_type: This line should not appear anywhere error_marker
    :param error_marker: error_marker
    """

    type: str = Field(
        default="sub-pipeline-component-correct-docstr",
        description=describe_attr("type", __doc__),
        const=True,
    )
    schema_type: Literal["sub-pipeline-component-correct-docstr"] = Field(  # type: ignore[assignment]
        default="sub-pipeline-component-correct-docstr",
        description=describe_object(__doc__),
        exclude=True,
    )


MODULE = EmptyPipelineComponent.__module__


@pytest.mark.filterwarnings("ignore:handlers", "ignore:config", "ignore:enrich")
class TestGenSchema:
    def test_gen_pipeline_schema_no_modules(self, caplog):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
                "--no-include-stock-components",
            ],
            catch_exceptions=False,
        )
        assert caplog.record_tuples == [("root", logging.WARNING, "No components are provided, no schema is generated.")]
        assert result.exit_code == 0

    def test_gen_pipeline_schema_only_stock_module(self):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
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

        assert result.exit_code == 0
        assert result.stdout

    def test_gen_pipeline_schema_only_custom_module(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            ["schema", "pipeline", MODULE, "--no-include-stock-components"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        snapshot.assert_match(result.stdout, "test-schema-generation")

    def test_gen_pipeline_schema_stock_and_custom_module(self):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
                MODULE,
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert result.stdout

    def test_gen_config_schema(self):
        result = runner.invoke(
            app,
            ["schema", "config"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
