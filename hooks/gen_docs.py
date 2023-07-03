"""Generates the whole 'generatable' KPOps documentation"""
import shutil
import subprocess
from pathlib import Path
from textwrap import fill
from typing import Any

from typer.models import ArgumentInfo, OptionInfo

from hooks import PATH_ROOT
from kpops.cli import main
from kpops.cli.pipeline_config import PipelineConfig

PATH_KPOPS_MAIN = PATH_ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = PATH_ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"
PATH_DOCS_VARIABLES = PATH_DOCS_RESOURCES / "variables"


#####################
# EXAMPLES          #
#####################


def write_title_to_file(
    file_path: Path, title: str, description: str, comment_symbol: str = "#"
) -> None:
    """Overwrite a file with a title and description as comments

    All previous contents will be erased!

    Example output:

    .. code-block:: python

        # Title
        #
        # Multi-line description of length 70
        # second line
        #
        VAR = None

    :param file_path: Path to the file
    :param title: Title
    :param description: File description
    :param comment_symbol: Symbol to use for comments, defaults to "#"
    """
    with open(file_path, "w+") as f:
        text = (
            f"{comment_symbol} "
            + title
            + f"\n{comment_symbol}\n"
            + fill(
                text=description,
                initial_indent=f"{comment_symbol} ",
                subsequent_indent=f"{comment_symbol} ",
            )
            + f"\n{comment_symbol}\n"
        )
        f.write(text)


def add_env_var_to_file(
    file_path: Path,
    description: str | list[str] | None,
    env_var_name: str,
    env_var_value: Any,
    comment_symbol: str = "#",
) -> None:
    """Adds an env var record and a description for it.

    If the value provided is ellipsis, a comment saying that
    the value is required is added

    :param file_path: Path to the file
    :param description: Variable description. If multiple sections are desired,
        provide them in a list.
    :param env_var_name: Name of the env variable
    :param env_var_value: Value to be assigned of the env var
    :param comment_symbol: Symbol to use for comments, defaults to "#"
    """
    with open(file_path, "a") as f:
        if description is not None:
            if isinstance(description, str):
                description = [description]
            for section in description:
                section = fill(
                    text=section,
                    initial_indent=f"{comment_symbol} ",
                    subsequent_indent=f"{comment_symbol} ",
                )
                f.write(section + "\n")
            # Dotenv has no `null` or `None` values, just leave the name of
            # the var alone there and it will be skipepd when reading
            # https://saurabh-kumar.com/python-dotenv/#file-format
            if env_var_value == Ellipsis:
                env_var_value = f" {comment_symbol} No default value, required"
            elif env_var_value is None:
                env_var_value = f" {comment_symbol} No default value, not required"
            else:
                env_var_value = f"={env_var_value}"

        f.write(f"{env_var_name}{env_var_value}\n")


# copy examples from tests resources
shutil.copyfile(
    PATH_ROOT / "tests/pipeline/resources/component-type-substitution/pipeline.yaml",
    PATH_DOCS_VARIABLES / "variable_substitution.yaml",
)

# find all config-related env variables and write them into a file
config_env_vars_file_path = PATH_DOCS_VARIABLES / "config_env_vars.env"
config_env_vars_title = "Pipeline config environment variables"
config_env_vars_description = (
    "The default setup is shown. "
    "These variables are an alternative to the settings in `config.yaml`. "
    "Variables marked as required can instead be set in the pipeline config."
)
write_title_to_file(
    config_env_vars_file_path, config_env_vars_title, config_env_vars_description
)
# NOTE: This does not see nested fields, hence if there are env vars in a class like
# TopicConfig(), they wil not be listed. Possible fix with recursion.
config_fields = PipelineConfig.__fields__
for config_field_name, config_field in config_fields.items():
    config_field_info = PipelineConfig.Config.get_field_info(config_field.name)
    config_field_description: str = (
        config_field_name
        + ": "
        + (
            config_field.field_info.description
            or "No description available, please refer to the pipeline config documentation."
        )
    )
    config_field_default = None or config_field.field_info.default
    if config_env_var := config_field_info.get(
        "env"
    ) or config_field.field_info.extra.get("env"):
        add_env_var_to_file(
            file_path=config_env_vars_file_path,
            description=config_field_description,
            env_var_name=config_env_var,
            env_var_value=config_field_default,
        )

# find all cli-related env variables, write them into a file
cli_env_vars_file_path = PATH_DOCS_VARIABLES / "cli_env_vars.env"
cli_env_vars_title = "CLI Environment variables"
cli_env_vars_description = (
    "The default setup is shown. These variables are a lower priority alternative to the commands' flags. "
    "If a variable is set, the corresponding flag does not have to be specified in commands. "
    "Variables marked as required can instead be set as flags."
)
write_title_to_file(
    cli_env_vars_file_path, cli_env_vars_title, cli_env_vars_description
)
for var_in_main_name in dir(main):
    var_in_main = getattr(main, var_in_main_name)
    if (
        not var_in_main_name.startswith("__")
        and isinstance(var_in_main, (OptionInfo, ArgumentInfo))
        and var_in_main.envvar
    ):
        cli_env_var_description: list[str] = [
            var_in_main.help
            or "No description available, please refer to the CLI Usage documentation"
        ]
        if isinstance(var_in_main.envvar, list):
            var_in_main_envvar = var_in_main.envvar[0]
            if len(var_in_main.envvar) > 1:
                cli_env_var_description = (
                    cli_env_var_description
                    + ["The following variables are equivalent:"]
                    + [
                        ", ".join(
                            [f"`{var_name}`" for var_name in var_in_main.envvar[1:]]
                        )
                    ]
                )
        else:
            var_in_main_envvar = var_in_main.envvar
        add_env_var_to_file(
            file_path=cli_env_vars_file_path,
            description=cli_env_var_description,
            env_var_name=var_in_main_envvar,
            env_var_value=var_in_main.default,
        )


#####################
# CLI-USAGE         #
#####################

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
