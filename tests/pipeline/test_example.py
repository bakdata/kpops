from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.utils.yaml_loading import load_yaml

runner = CliRunner()


class TestExample:
    def test_atm_fraud(self, snapshot: SnapshotTest):
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
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        enriched_pipeline = load_yaml(result.stdout)
        snapshot.assert_match(enriched_pipeline, "atm-fraud-pipeline")
