from __future__ import annotations

import logging
from pathlib import Path

import pytest
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components import PipelineComponent

RESOURCE_PATH = Path(__file__).parent / "resources"


runner = CliRunner()


# type is inherited from PipelineComponent
class EmptyPipelineComponent(PipelineComponent):
    class Config:
        anystr_strip_whitespace = True


class SubPipelineComponent(EmptyPipelineComponent):
    ...


# type is inherited from SubPipelineComponent
class SubPipelineComponentNoSchemaTypeNoType(SubPipelineComponent):
    ...


# Correctly defined
class SubPipelineComponentCorrect(SubPipelineComponent):
    ...


# Correctly defined, docstr test
class SubPipelineComponentCorrectDocstr(SubPipelineComponent):
    """
    Newline before title is removed

    Summarry is correctly imported.
        All
            whitespaces are      removed and replaced with a single space.

    The description extraction terminates at the correct place, deletes 1 trailing coma

    ,

    :param error_marker: error_marker
    """


MODULE = EmptyPipelineComponent.__module__


@pytest.mark.filterwarnings(
    "ignore:handlers", "ignore:config", "ignore:enrich", "ignore:validate"
)
class TestGenSchema:
    def test_gen_pipeline_schema_no_modules(self, caplog: pytest.LogCaptureFixture):
        result = runner.invoke(
            app,
            [
                "schema",
                "pipeline",
                "--no-include-stock-components",
            ],
            catch_exceptions=False,
        )
        assert caplog.record_tuples == [
            (
                "root",
                logging.WARNING,
                "No components are provided, no schema is generated.",
            )
        ]
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
        assert result.stdout
