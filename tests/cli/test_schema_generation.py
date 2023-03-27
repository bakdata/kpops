from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
from pydantic import Field
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components import PipelineComponent

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


# schema_type is ineritted from sub-pipeline-component
class SubPipelineComponentNoSchemaType(SubPipelineComponent):
    type: str = "sub-pipeline-component-no-schema-type"


# schema_type and type are ineritted from sub-pipeline-component
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


MODULE = EmptyPipelineComponent.__module__


@pytest.mark.filterwarnings("ignore:handlers", "ignore:config", "ignore:enrich")
class TestGenSchema:
    def test_gen_pipeline_schema_without_custom_module(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        snapshot.assert_match(result.stdout, "test-schema-generation")

    def test_gen_pipeline_schema_with_custom_module(self, snapshot: SnapshotTest):
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

        snapshot.assert_match(result.stdout, "test-schema-generation")

    def test_gen_config_schema(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            ["schema", "config"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        snapshot.assert_match(result.stdout, "test-schema-generation")
