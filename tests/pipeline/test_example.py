import os
from pathlib import Path

import pytest
import yaml
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app

runner = CliRunner()

EXAMPLES_PATH = Path("examples").absolute()


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache")
class TestExample:
    @pytest.fixture(scope="class", autouse=True)
    def cd(self):
        cwd = Path.cwd().absolute()
        os.chdir(EXAMPLES_PATH)
        yield
        os.chdir(cwd)

    def test_cwd(self):
        assert Path.cwd() == EXAMPLES_PATH

    def test_atm_fraud(self, snapshot: SnapshotTest):
        result = runner.invoke(
            app,
            [
                "generate",
                "atm-fraud/pipeline.yaml",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        enriched_pipeline: dict = yaml.safe_load(result.stdout)
        snapshot.assert_match(enriched_pipeline, "atm-fraud-pipeline")
