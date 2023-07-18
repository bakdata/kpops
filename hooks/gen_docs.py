"""Generates the whole 'generatable' KPOps documentation."""
import shutil
import subprocess
from csv import reader, writer
from enum import StrEnum
from pathlib import Path
from textwrap import fill
from typing import Any, NamedTuple

from pytablewriter import MarkdownTableWriter
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


class EnvVar(NamedTuple):
    name: str
    default_value: Any
    required: bool
    description: str | None
    corresponding_setting_name: str | None


class EnvVarAttrs(StrEnum):
    NAME = "Name"
    DEFAULT_VALUE = "Default Value"
    REQUIRED = "Required"
    DESCRIPTION = "Description"
    CORRESPONDING_SETTING_NAME = "Setting name"


def csv_append_env_var(
    file: Path, name: str, default_value, description: str | list[str] | None, *args
) -> None:
    """Append env variable record to a chosen .csv file, create it if doesn't exist.

    :param file: csv_file
    :param name: env var name
    :param default_value: Default value of the env var
    :param description: Text description of the env var
    :param args: Any additional fields to be added to the csv file
    """
    formatted_description = ""
    if description is not None:
        if isinstance(description, str):
            description = [description]
        for section in description:
            formatted_description += fill(
                text=section,
                width=68,
            )
    required = False
    if default_value == Ellipsis:
        required = True
        default_value = ""
    elif default_value is None:
        default_value = ""
    with file.open("a+") as csv_file:
        writer(csv_file).writerow(
            [name, default_value, required, formatted_description, *list(args)]
        )


def write_title_to_dotenv_file(
    file_path: Path,
    title: str,
    description: str,
    comment_symbol: str = "#",
) -> None:
    """Overwrite a file with a title and description as comments.

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


def append_csv_to_dotenv_file(
    source: Path,
    target: Path,
) -> None:
    """Parses csv file looking for a env variable records and appends them into a dotenv file

    :param source: csv file to read from
    :param target: dotenv file to wread into
    """
    comment_symbol = "#"  # Comments in .env start with a `#`
    with source.open("r") as s_target:
        r = reader(s_target)
        columns = next(r)
        for line in r:
            record = dict(zip(columns, line))
            env_var = EnvVar(
                name=record[EnvVarAttrs.NAME],
                default_value=record[EnvVarAttrs.DEFAULT_VALUE],
                required=record[EnvVarAttrs.REQUIRED] == "True",
                description=record[EnvVarAttrs.DESCRIPTION],
                corresponding_setting_name=record.get(
                    EnvVarAttrs.CORRESPONDING_SETTING_NAME
                ),
            )
            env_var = env_var._replace(
                description=fill(
                    text=env_var.description,
                    initial_indent=f"{comment_symbol} ",
                    subsequent_indent=f"{comment_symbol} ",
                )
            )
            if env_var.corresponding_setting_name:
                env_var = env_var._replace(
                    description=f"# {env_var.corresponding_setting_name}\n{env_var.description}"
                )
            # Dotenv has no `null` or `None` values, just leave the name of
            # the var alone there and it will be skipepd when reading
            # https://saurabh-kumar.com/python-dotenv/#file-format
            if env_var.required and not env_var.default_value:
                default_value = f" {comment_symbol} No default value, required"
            elif not env_var.default_value:
                default_value = f" {comment_symbol} No default value, not required"
            else:
                default_value = f"={env_var.default_value}"
            env_var = env_var._replace(default_value=default_value)
            with target.open("a") as f_target:
                f_target.write(
                    f"{env_var.description}\n"
                    f"{env_var.name}{env_var.default_value}\n",
                )


def write_md_table_to_file(title, description, headers):  # TODO(@sujuka99): implement
    MarkdownTableWriter(
        table_name=title,
        headers=headers,
        value_matrix=[],
    )


# copy examples from tests resources
shutil.copyfile(
    PATH_ROOT / "tests/pipeline/resources/component-type-substitution/pipeline.yaml",
    PATH_DOCS_VARIABLES / "variable_substitution.yaml",
)

# find all config-related env variables and write them into a file
PATH_CONFIG_ENV_VARS_DOTENV_FILE = PATH_DOCS_VARIABLES / "config_env_vars.env"
PATH_CONFIG_ENV_VARS_CSV_FILE = PATH_DOCS_VARIABLES / "temp_config_env_vars.csv"
CONFIG_ENV_VARS_TITLE = "Pipeline config environment variables"
CONFIG_ENV_VARS_DESCRIPTION = (
    "The default setup is shown. "
    "These variables are an alternative to the settings in `config.yaml`. "
    "Variables marked as required can instead be set in the pipeline config."
)
# Overwrite the temp csv file
with PATH_CONFIG_ENV_VARS_CSV_FILE.open("w+") as f:
    writer(f).writerow(
        [
            EnvVarAttrs.NAME,
            EnvVarAttrs.DEFAULT_VALUE,
            EnvVarAttrs.REQUIRED,
            EnvVarAttrs.DESCRIPTION,
            EnvVarAttrs.CORRESPONDING_SETTING_NAME,
        ]
    )
write_title_to_dotenv_file(
    PATH_CONFIG_ENV_VARS_DOTENV_FILE,
    CONFIG_ENV_VARS_TITLE,
    CONFIG_ENV_VARS_DESCRIPTION,
)
# NOTE: This does not see nested fields, hence if there are env vars in a class like
# TopicConfig(), they wil not be listed. Possible fix with recursion.
config_fields = PipelineConfig.__fields__
for config_field_name, config_field in config_fields.items():
    config_field_info = PipelineConfig.Config.get_field_info(config_field.name)
    config_field_description: str = (
        config_field.field_info.description
        or "No description available, please refer to the pipeline config documentation."
    )
    config_field_default = None or config_field.field_info.default
    if config_env_var := config_field_info.get(
        "env",
    ) or config_field.field_info.extra.get("env"):
        csv_append_env_var(
            PATH_CONFIG_ENV_VARS_CSV_FILE,
            config_env_var,
            config_field_default,
            config_field_description,
            config_field_name,
        )
append_csv_to_dotenv_file(
    PATH_CONFIG_ENV_VARS_CSV_FILE, PATH_CONFIG_ENV_VARS_DOTENV_FILE
)

# find all cli-related env variables, write them into a file
PATH_CLI_ENV_VARS_DOTFILES_FILE = PATH_DOCS_VARIABLES / "cli_env_vars.env"
PATH_CLI_ENV_VARS_CSV_FILE = PATH_DOCS_VARIABLES / "temp_cli_env_vars.csv"
CLI_ENV_VARS_TITLE = "CLI Environment variables"
CLI_ENV_VARS_DESCRIPTION = (
    "The default setup is shown. These variables are a lower priority alternative to the commands' flags. "
    "If a variable is set, the corresponding flag does not have to be specified in commands. "
    "Variables marked as required can instead be set as flags."
)
# Overwrite the temp csv file
with PATH_CLI_ENV_VARS_CSV_FILE.open("w+") as f:
    writer(f).writerow(
        [
            EnvVarAttrs.NAME,
            EnvVarAttrs.DEFAULT_VALUE,
            EnvVarAttrs.REQUIRED,
            EnvVarAttrs.DESCRIPTION,
            EnvVarAttrs.CORRESPONDING_SETTING_NAME,
        ]
    )
write_title_to_dotenv_file(
    PATH_CLI_ENV_VARS_DOTFILES_FILE,
    CLI_ENV_VARS_TITLE,
    CLI_ENV_VARS_DESCRIPTION,
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
            or "No description available, please refer to the CLI Usage documentation",
        ]
        if isinstance(var_in_main.envvar, list):
            var_in_main_envvar = var_in_main.envvar[0]
            if len(var_in_main.envvar) > 1:
                cli_env_var_description = [
                    *cli_env_var_description,
                    f"The following variables are equivalent to {var_in_main_envvar}:",
                    ", ".join([f"`{var_name}`" for var_name in var_in_main.envvar[1:]]),
                ]
        else:
            var_in_main_envvar = var_in_main.envvar
        csv_append_env_var(
            PATH_CLI_ENV_VARS_CSV_FILE,
            var_in_main_envvar,
            var_in_main.default,
            cli_env_var_description,
        )
append_csv_to_dotenv_file(PATH_CLI_ENV_VARS_CSV_FILE, PATH_CLI_ENV_VARS_DOTFILES_FILE)


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
