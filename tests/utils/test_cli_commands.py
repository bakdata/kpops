from pathlib import Path

from kpops.utils.cli_commands import create_config, init_project


def test_init_project(tmp_path):
    init_project(tmp_path, True)
    for path in ["config.yaml", "defaults.yaml", "pipeline.yaml"]:
        assert Path(tmp_path / path).exists()


def test_create_config(tmp_path):
    opt_conf_name = "config_with_non_required"
    req_conf_name = "config_with_only_required"
    create_config(opt_conf_name, tmp_path, True)
    create_config(req_conf_name, tmp_path, False)
    assert (opt_conf := Path(tmp_path / (opt_conf_name + ".yaml"))).exists()
    assert (req_conf := Path(tmp_path / (req_conf_name + ".yaml"))).exists()
    with opt_conf.open() as opt_file, req_conf.open() as req_file:
        assert len(opt_file.readlines()) > len(req_file.readlines())
