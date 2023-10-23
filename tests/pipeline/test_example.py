import pytest
import yaml
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app

runner = CliRunner()


@pytest.mark.usefixtures("mock_env")
class TestExample:
    def test_atm_fraud(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "./examples/bakdata/atm-fraud-detection/pipeline.yaml",
                "--pipeline-base-dir",
                "examples",
                "--config",
                "./examples/bakdata/atm-fraud-detection/config.yaml",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "atm-fraud-pipeline")
