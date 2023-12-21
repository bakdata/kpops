
import logging
from pathlib import Path
from hooks.gen_docs.gen_docs_env_vars import collect_fields

from kpops.cli.pipeline_config import PipelineConfig

log = logging.getLogger("cli_commands_utils")
    
def touch_yaml_file(file_name, dir_path) -> Path:
    file_path = Path(dir_path / (file_name + ".yaml"))
    file_path.touch(exist_ok=False)
    return file_path

def create_config(file_name: str, dir_path: Path) -> None:
    file_path = touch_yaml_file(file_name, dir_path)
    config_fields = collect_fields(PipelineConfig)
    with file_path.open(mode="w"):
        


def create_defaults(file_name: str, dir_path: Path) -> None:
    file_path = touch_yaml_file(file_name, dir_path)

def create_pipeline(file_name: str, dir_path: Path) -> None:
    file_path = touch_yaml_file(file_name, dir_path)
