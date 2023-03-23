from __future__ import annotations

from pathlib import Path
from typing import Literal

import pytest
import json
import warnings
from pydantic import Field
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components import PipelineComponent

RESOURCE_PATH = Path(__file__).parent / "resources"


runner = CliRunner()


class SubComponent(PipelineComponent):
    type: str = "sub-component"
    schema_type: Literal["sub-component"] = Field(  # type: ignore[assignment]
        default="sub-component", exclude=True
    )

MODULE = SubComponent.__module__

class SubSubComponent(SubComponent):
    type: str = "sub-sub-component"
    schema_type: Literal["sub-sub-component"] = Field(  # type: ignore[assignment]
        default="sub-sub-component", exclude=True
    )


class Unrelated:
    pass

@pytest.mark.filterwarnings("ignore:handlers", "ignore:config", "ignore:enrich")
class TestGenSchema:
    def test_gen_pipeline_schema_without_custom_module(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "gen-schema",
                "--path",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        schema_path = RESOURCE_PATH / "pipeline.json"

        with open(schema_path, "r") as schema:
            generated_schema = json.load(schema)

        snapshot.assert_match(generated_schema, "test-schema-generation")
        try:
            schema_path.unlink()
        except FileNotFoundError:
            pytest.fail(
                f"File {schema_path} did not get generated."
            )

    def test_gen_pipeline_schema_with_custom_module(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "gen-schema",
                MODULE,
                "--path",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        schema_path = RESOURCE_PATH / "pipeline.json"

        with open(schema_path, "r") as schema:
            generated_schema = json.load(schema)

        snapshot.assert_match(generated_schema, "test-schema-generation")

        try:
            schema_path.unlink()
        except FileNotFoundError:
            pytest.fail(
                f"File {schema_path} did not get generated."
            )

    def test_gen_config_schema(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "gen-schema",
                MODULE,
                "--no-pipeline",
                "--config",
                "--path",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        schema_path = RESOURCE_PATH / "config.json"

        with open(schema_path, "r") as schema:
            generated_schema = json.load(schema)

        snapshot.assert_match(generated_schema, "test-schema-generation")

        try:
            schema_path.unlink()
        except FileNotFoundError:
            pytest.fail(
                f"File {schema_path} did not get generated."
            )
