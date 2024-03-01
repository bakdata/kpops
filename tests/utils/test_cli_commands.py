from pathlib import Path

from typer.testing import CliRunner

import kpops
from kpops.cli.main import app
from kpops.utils.cli_commands import create_config

runner = CliRunner()


def test_create_config(tmp_path: Path):
    opt_conf_name = "config_with_non_required"
    req_conf_name = "config_with_only_required"
    create_config(opt_conf_name, tmp_path, True)
    create_config(req_conf_name, tmp_path, False)
    assert (opt_conf := Path(tmp_path / (opt_conf_name + ".yaml"))).exists()
    assert (req_conf := Path(tmp_path / (req_conf_name + ".yaml"))).exists()
    with opt_conf.open() as opt_file, req_conf.open() as req_file:
        assert len(opt_file.readlines()) > len(req_file.readlines())


def test_init_project(tmp_path: Path):
    kpops.init(tmp_path, config_include_opt=True)
    for path in ["config.yaml", "defaults.yaml", "pipeline.yaml"]:
        assert Path(tmp_path / path).exists()


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
