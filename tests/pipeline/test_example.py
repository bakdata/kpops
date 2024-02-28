import os
from pathlib import Path

import pytest
from pytest_snapshot.plugin import Snapshot
from typer.testing import CliRunner

import kpops

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

    @pytest.fixture(scope="session")
    def test_submodule(self):
        assert any(
            EXAMPLES_PATH.iterdir()
        ), "examples directory is empty, please initialize and update the git submodule (see contributing guide)"

    @pytest.mark.usefixtures("test_submodule")
    def test_word_count(self, snapshot: Snapshot):
        pipeline = kpops.generate(Path("word-count/pipeline.yaml"))
        snapshot.assert_match(pipeline.to_yaml(), "pipeline.yaml")

    @pytest.mark.usefixtures("test_submodule")
    def test_atm_fraud(self, snapshot: Snapshot):
        pipeline = kpops.generate(Path("atm-fraud/pipeline.yaml"))
        snapshot.assert_match(pipeline.to_yaml(), "pipeline.yaml")
