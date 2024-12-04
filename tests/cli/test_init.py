from pathlib import Path

import pytest
from pytest_snapshot.plugin import Snapshot
from typer.testing import CliRunner

import kpops.api as kpops
from kpops.cli.main import app
from kpops.utils.cli_commands import create_config

runner = CliRunner()


def test_create_config(tmp_path: Path):
    opt_conf_name = "config_with_non_required"
    req_conf_name = "config_with_only_required"
    create_config(opt_conf_name, tmp_path, True)
    create_config(req_conf_name, tmp_path, False)
    opt_conf = (tmp_path / opt_conf_name).with_suffix(".yaml")
    assert opt_conf.exists()
    req_conf = (tmp_path / req_conf_name).with_suffix(".yaml")
    assert req_conf.exists()
    assert len(opt_conf.read_text()) > len(req_conf.read_text())


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache", "clear_kpops_config")
def test_init_project_exclude_optional(tmp_path: Path, snapshot: Snapshot):
    req_path = tmp_path / "req"
    req_path.mkdir()
    kpops.init(req_path, config_include_optional=False)
    snapshot.assert_match(Path(req_path / "config.yaml").read_text(), "config.yaml")
    snapshot.assert_match(Path(req_path / "pipeline.yaml").read_text(), "pipeline.yaml")
    snapshot.assert_match(Path(req_path / "defaults.yaml").read_text(), "defaults.yaml")


def test_init_project_include_optional(tmp_path: Path, snapshot: Snapshot):
    opt_path = tmp_path / "opt"
    opt_path.mkdir()
    kpops.init(opt_path, config_include_optional=True)
    snapshot.assert_match(Path(opt_path / "config.yaml").read_text(), "config.yaml")
    snapshot.assert_match(Path(opt_path / "pipeline.yaml").read_text(), "pipeline.yaml")
    snapshot.assert_match(Path(opt_path / "defaults.yaml").read_text(), "defaults.yaml")


def test_init_project_from_cli_with_bad_path(tmp_path: Path):
    bad_path = Path(tmp_path / "random_file.yaml")
    bad_path.touch()
    result = runner.invoke(
        app,
        [
            "init",
            str(bad_path),
        ],
        catch_exceptions=False,
    )
    assert result.exit_code == 2
