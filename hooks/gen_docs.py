"""Generates the whole 'generatable' KPOps documentation"""
import shutil
import subprocess

from typer.models import ArgumentInfo, OptionInfo

from hooks import PATH_ROOT
from kpops.cli import main
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
with open(PATH_DOCS_VARIABLES / "config_env_vars.env", "w+") as f:
    f.write(
        "# Pipeline config environment variables\n#\n# The default setup is shown."
        "\n# These variables are an alternative to the settings in `config.yaml`.\n#\n"
    )
fields = PipelineConfig.__fields__
env_vars: dict[str, str] = {}
for name, field in fields.items():
    field_info_from_config = PipelineConfig.Config.get_field_info(field.name)
    env = field_info_from_config.get("env") or field.field_info.extra.get("env")
    description = (
        field.field_info.description
        or "No description available, please refer to the pipeline config documentation."
    )
    default = field.field_info.default or "None"
    if env:
        with open(PATH_DOCS_VARIABLES / "config_env_vars.env", "a") as f:
            f.write(f"# {name}: {description}\n")
            f.write(f"{env} = {default}\n")

# find all cli-related env variables, write them into a file
vars_in_main = [item for item in dir(main) if not item.startswith("__")]
with open(
    PATH_DOCS_VARIABLES / "cli_env_vars.env", "w+"
) as f:  # delete the contents of the file
    f.write(
        "# CLI Environment variables\n#\n# The default setup is shown.\n"
        "# These variables are an alternative to the commands' flags.\n#\n"
    )
for item in vars_in_main:
    var = getattr(main, item)
    if (
        not item.startswith("__")
        and isinstance(var, (OptionInfo, ArgumentInfo))
        and var.envvar
    ):
        with open(
            PATH_DOCS_VARIABLES / "cli_env_vars.env", "a"
        ) as f:  # delete the contents of the file
            f.write(f"# {var.help}\n")
            f.write(f"{var.envvar} = {var.default}\n")
