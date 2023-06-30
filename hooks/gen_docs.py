"""Generates the whole 'generatable' KPOps documentation"""
from pprint import pprint
import shutil
import subprocess

import yaml

from hooks import PATH_ROOT
from kpops.cli.pipeline_config import PipelineConfig

PATH_KPOPS_MAIN = PATH_ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = PATH_ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"
PATH_DOCS_VARIABLES = PATH_DOCS_RESOURCES / "variables"

# Run typer-cli on kpops to generate doc on CLI usage
# TODO: try to use typer_cli.main.docs here instead
typer_args: list[str] = [
    "typer",
    str(PATH_KPOPS_MAIN),
    "utils",
    "docs",
    "--name",
    "kpops",
    "--output",
    str(PATH_CLI_COMMANDS_DOC),
]
subprocess.run(typer_args)

# Replace wrong title in CLI Usage doc
with open(PATH_CLI_COMMANDS_DOC, "r") as f:
    text = f.readlines()
text[0] = "# CLI Usage\n"
with open(PATH_CLI_COMMANDS_DOC, "w") as f:
    f.writelines(text)


# copy examples from tests resources
shutil.copyfile(
    PATH_ROOT / "tests/pipeline/resources/component-type-substitution/pipeline.yaml",
    PATH_DOCS_VARIABLES / "variable_substitution.yaml",
)

# find all config-related env variables and write them into a file
fields = PipelineConfig.__fields__
env_vars: dict[str, str] = {}
for name, field in fields.items():
    field_info_from_config = PipelineConfig.Config.get_field_info(field.name)
    env = field_info_from_config.get('env') or field.field_info.extra.get('env')
    if env:
        env_vars[name] = env
with open(PATH_DOCS_VARIABLES / "config_env_vars.yaml", "w+") as f:
    yaml.dump(env_vars, f)
