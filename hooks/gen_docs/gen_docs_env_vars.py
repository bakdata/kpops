"""Generates the documentation on KPOps environment variables."""

import csv
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from textwrap import fill
from typing import Any

from pytablewriter import MarkdownTableWriter
from typer.models import ArgumentInfo, OptionInfo
from typing_extensions import Self

from hooks import PATH_ROOT
from hooks.gen_docs import SuperEnum
from kpops.cli import main
from kpops.cli.pipeline_config import PipelineConfig

PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"
PATH_DOCS_VARIABLES = PATH_DOCS_RESOURCES / "variables"

PATH_CONFIG_ENV_VARS_DOTENV_FILE = PATH_DOCS_VARIABLES / "config_env_vars.env"
PATH_CONFIG_ENV_VARS_MD_FILE = PATH_DOCS_VARIABLES / "config_env_vars.md"
PATH_CONFIG_ENV_VARS_CSV_FILE = PATH_DOCS_VARIABLES / "temp_config_env_vars.csv"
TITLE_CONFIG_ENV_VARS = "Pipeline config environment variables"
DESCRIPTION_CONFIG_ENV_VARS = (
    "These variables are a lower priority alternative to the settings in `config.yaml`. "
    "Variables marked as required can instead be set in the pipeline config."
)

PATH_CLI_ENV_VARS_DOTFILES_FILE = PATH_DOCS_VARIABLES / "cli_env_vars.env"
PATH_CLI_ENV_VARS_MD_FILE = PATH_DOCS_VARIABLES / "cli_env_vars.md"
PATH_CLI_ENV_VARS_CSV_FILE = PATH_DOCS_VARIABLES / "temp_cli_env_vars.csv"
TITLE_CLI_ENV_VARS = "CLI Environment variables"
DESCRIPTION_CLI_ENV_VARS = (
    "These variables are a lower priority alternative to the commands' flags. "
    "If a variable is set, the corresponding flag does not have to be specified in commands. "
    "Variables marked as required can instead be set as flags."
)

# Descriptions for the tables and the dotenv files are the same, except for the
# sentence bellow
DESCRIPTION_ADDITION_DOTENV_FILE = "The default setup is shown. "

COMMENT_SYMBOL = "#"


@dataclass
class EnvVar:
    """Environment variable's properties.

    :param name: Name of the vaiable
    :param default_value: Default value of the variable
    :param required: Whether it is required to set the var
    :param description: Description of the variable
    :param corresponding_setting_name: What, if any, setting(s)
        the variable controls
    """

    name: str
    default_value: Any
    required: bool
    description: str | None
    corresponding_setting_name: str | None

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> Self:
        """Construct an ``EnvVar`` instance from a specific dict.

        Reads a dict that contains keys equivalent to the
        attributes of ``cls``, but under different names.
        The names are set in ``EnvVarAttrs``.

        :param record: Dict to use in the constructor
        :return: An ``EnvVar`` instance
        """
        return cls(
            name=record[EnvVarAttrs.NAME],
            default_value=record[EnvVarAttrs.DEFAULT_VALUE],
            required=record[EnvVarAttrs.REQUIRED] == "True",
            description=record[EnvVarAttrs.DESCRIPTION],
            corresponding_setting_name=record.get(
                EnvVarAttrs.CORRESPONDING_SETTING_NAME,
            ),
        )


class EnvVarAttrs(str, SuperEnum):
    """The attr names are used as columns for the markdown tables."""

    NAME = "Name"
    DEFAULT_VALUE = "Default Value"
    REQUIRED = "Required"
    DESCRIPTION = "Description"
    CORRESPONDING_SETTING_NAME = "Setting name"


def csv_append_env_var(
    file: Path,
    name: str,
    default_value,
    description: str | list[str] | None,
    *args,
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
        csv.writer(csv_file).writerow(
            [name, default_value, required, formatted_description, *list(args)],
        )


def write_title_to_dotenv_file(
    file_path: Path,
    title: str,
    description: str,
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
    """
    with file_path.open("w+") as f:
        text = (
            f"{COMMENT_SYMBOL} {title}"
            f"\n{COMMENT_SYMBOL}\n"
            + fill(
                text=description,
                initial_indent=f"{COMMENT_SYMBOL} ",
                subsequent_indent=f"{COMMENT_SYMBOL} ",
            )
            + f"\n{COMMENT_SYMBOL}\n"
        )
        f.write(text)


def append_csv_to_dotenv_file(
    source: Path,
    target: Path,
) -> None:
    """Parse csv file looking for a env variable records and append them into a dotenv file.

    :param source: csv file to read from
    :param target: dotenv file to wread into
    """
    with source.open("r") as s_target:
        r = csv.reader(s_target)
        columns = next(r)
        for line in r:
            record = dict(zip(columns, line, strict=True))
            env_var = EnvVar.from_record(record)
            env_var.description = fill(
                text=env_var.description or "",
                initial_indent=f"{COMMENT_SYMBOL} ",
                subsequent_indent=f"{COMMENT_SYMBOL} ",
            )
            if env_var.corresponding_setting_name:
                env_var.description = (
                    f"# {env_var.corresponding_setting_name}\n{env_var.description}"
                )
            # Dotenv has no `null` or `None` values, just leave the name of
            # the var alone there and it will be skipped when reading
            # https://saurabh-kumar.com/python-dotenv/#file-format
            if env_var.required and not env_var.default_value:
                default_value = f" {COMMENT_SYMBOL} No default value, required"
            elif not env_var.default_value:
                default_value = f" {COMMENT_SYMBOL} No default value, not required"
            else:
                default_value = f"={env_var.default_value}"
            env_var.default_value = default_value
            with target.open("a") as f_target:
                f_target.write(
                    f"{env_var.description}\n"
                    f"{env_var.name}{env_var.default_value}\n",
                )


def write_csv_to_md_file(
    source: Path,
    target: Path,
    title: str | None,
    description: str | None = None,
    heading: str = "###",
) -> None:
    """Write csv data from a file into a markdown file.

    :param source: path to csv file to read from
    :param target: path to md file to overwrite or create
    :param title: Title for the table, optional

    """
    with target.open("w+") as f:
        if title:
            f.write(f"{heading} {title}\n")
        if description:
            f.write(f"\n{description}\n\n")
        writer = MarkdownTableWriter()
        writer.from_csv(str(source))
        writer.table_name = ""
        writer.dump(output=f)


def __fill_csv_pipeline_config(target: Path) -> None:
    """Append all ``PipelineConfig``-related env vars to a ``.csv`` file.

    Finds all ``PipelineConfig``-related env vars and appends them to
    a ``.csv`` file.

    :param target: The path to the `.csv` file. Note that it must already
        contain the column names
    """
    # NOTE: This does not see nested fields, hence if there are env vars in a class like
    # TopicConfig(), they wil not be listed. Possible fix with recursion.
    config_fields = PipelineConfig.__fields__
    for config_field in config_fields.values():
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
                target,
                config_env_var,
                config_field_default,
                config_field_description,
                config_field.name,
            )


def __fill_csv_cli(target: Path) -> None:
    """Append all CLI-commands-related env vars to a ``.csv`` file.

    Finds all CLI-commands-related env vars and appends them to a ``.csv``

    :param target: The path to the `.csv` file. Note that it must already
        contain the column names
    """
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
                        ", ".join(
                            [f"`{var_name}`" for var_name in var_in_main.envvar[1:]],
                        ),
                    ]
            else:
                var_in_main_envvar = var_in_main.envvar
            csv_append_env_var(
                target,
                var_in_main_envvar,
                var_in_main.default,
                cli_env_var_description,
            )


def gen_vars(
    dotenv_file: Path,
    md_file: Path,
    csv_file: Path,
    title_dotenv_file: str,
    description_dotenv_file: str,
    columns: list,
    description_md_file: str,
    variable_extraction_function: Callable[[Path], None],
) -> None:
    """Write env var documentation in both a markdown table and a dotenv file.

    :param dotenv_file: Path of the dotenv file
    :param md_file: Path of the md file
    :param csv_file: Path for a temp CSV file, will be deleted after
        a successful execution.
        **WARNING** If a file with this path exists, it will be permanently deleted
    :param title_dotenv_file: The title for the dotenv file
    :param description_dotenv_file: The description to be written in the dotenv file
    :param columns: The column names in the table
    :param description_md_file: The description to be written in the markdown file
    :param variable_extraction_function: Function that ooks for variables and appends
        them to the temp csv file.
    """
    # Overwrite/create the temp csv file
    with csv_file.open("w+") as f:
        csv.writer(f).writerow(columns)
    write_title_to_dotenv_file(
        dotenv_file,
        title_dotenv_file,
        description_dotenv_file,
    )
    variable_extraction_function(csv_file)
    append_csv_to_dotenv_file(
        csv_file,
        dotenv_file,
    )
    write_csv_to_md_file(
        source=csv_file,
        target=md_file,
        title=None,
        description=description_md_file,
    )
    # Delete the csv file, it is not useful anymore
    csv_file.unlink(missing_ok=True)


if __name__ == "__main__":
    # copy examples from tests resources
    shutil.copyfile(
        PATH_ROOT
        / "tests/pipeline/resources/component-type-substitution/pipeline.yaml",
        PATH_DOCS_VARIABLES / "variable_substitution.yaml",
    )
    # Find all config-related env variables and write them into a file
    gen_vars(
        dotenv_file=PATH_CONFIG_ENV_VARS_DOTENV_FILE,
        md_file=PATH_CONFIG_ENV_VARS_MD_FILE,
        csv_file=PATH_CONFIG_ENV_VARS_CSV_FILE,
        title_dotenv_file=TITLE_CONFIG_ENV_VARS,
        description_dotenv_file=DESCRIPTION_ADDITION_DOTENV_FILE
        + DESCRIPTION_CONFIG_ENV_VARS,
        columns=list(EnvVarAttrs.values()),
        description_md_file=DESCRIPTION_CONFIG_ENV_VARS,
        variable_extraction_function=__fill_csv_pipeline_config,
    )
    # Find all cli-related env variables, write them into a file
    gen_vars(
        dotenv_file=PATH_CLI_ENV_VARS_DOTFILES_FILE,
        md_file=PATH_CLI_ENV_VARS_MD_FILE,
        csv_file=PATH_CLI_ENV_VARS_CSV_FILE,
        title_dotenv_file=TITLE_CLI_ENV_VARS,
        description_dotenv_file=DESCRIPTION_ADDITION_DOTENV_FILE
        + DESCRIPTION_CLI_ENV_VARS,
        columns=list(EnvVarAttrs.values())[:-1],
        description_md_file=DESCRIPTION_CLI_ENV_VARS,
        variable_extraction_function=__fill_csv_cli,
    )
