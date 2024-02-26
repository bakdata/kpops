from pathlib import Path

from kpops.utils.cli_commands import create_config, init_project


def test_init_project(tmp_path):
    init_project(tmp_path, True)
    for path in ["config.yaml", "defaults.yaml", "pipeline.yaml"]:
        assert Path(tmp_path / path).exists()

def test_create_config(tmp_path):
    opt_conf = "config_with_non_required.yaml"
    req_conf = "config_with_only_required.yaml"
    create_config(opt_conf , tmp_path, True)
    create_config(req_conf , tmp_path, False)

