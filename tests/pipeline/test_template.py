from pathlib import Path

import yaml
from snapshottest.module import SnapshotTest
from typer.testing import CliRunner

from kpops.cli.main import app

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"
PIPELINE_BASE_DIR = str(RESOURCE_PATH.parent)

class TestTemplate:
    def test_default_template_config(self):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--template",
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0


    def test_template_config_with_flags(self):
        result = runner.invoke(
            app,
            [
                "generate",
                "--pipeline-base-dir",
                PIPELINE_BASE_DIR,
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--template",
                "--api-version",
                "2.1.1",
                "--ca-file",
                "ca-file",
                "--cert-file",
                "cert-file"
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
