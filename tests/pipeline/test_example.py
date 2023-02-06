from pathlib import Path

import pytest
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.utils.yaml_loading import load_yaml_file

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"
PIPELINE_BASE_DIR = str(RESOURCE_PATH.parent)


class TestExample:
    @pytest.fixture
    def output_file_path(self, tmp_path: Path) -> Path:
        return tmp_path / "pipeline.yaml"

    def test_atm_fraud(self, output_file_path: Path, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "./examples/bakdata/atm-fraud-detection/pipeline.yaml",
                "--pipeline-base-dir",
                "examples",
                "--defaults",
                "./examples/bakdata/atm-fraud-detection/defaults",
                "--config",
                "./examples/bakdata/atm-fraud-detection/config.yaml",
                "--save",
                "--out-path",
                str(output_file_path),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = load_yaml_file(output_file_path)
        snapshot.assert_match(enriched_pipeline, "atm-fraud-pipeline")
