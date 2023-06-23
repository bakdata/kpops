"""Generates the whole 'generatable' KPOps documentation"""
import os
import subprocess
from enum import Enum
from pathlib import Path

from hooks import PATH_ROOT

PATH_KPOPS_MAIN = PATH_ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = PATH_ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"
PATH_DOCS_PIPELINE_COMPONENTS = PATH_DOCS_RESOURCES / "pipeline-components"
SECTIONS_ORDER = [
    "type",
    "name",
    "namespace",
    "app",
    "from",
    "to",
    "prefix",
    "repo-config",
    "version",
    "resetter-values",
    "offset-topic",
]


# class Section(Enum):
#     TYPE = "type"
#     NAME = "name"
#     NAMESPACE = "namespace"
#     APP = "app"
#     TO = "to"
#     PREFIX = "prefix"
#     REPO_CONFIG = "repo-config"
#     VERSION = "version"
#     RESETTER_VALUES = "resetter-values"
#     OFFSET_TOPIC = "offset-topic"


def concatenate_text_files(*file_paths: Path, target: Path):
    """Concatenates the given files into one

    :param *file_paths: Files to be conatenated. The order of the inputs will be
        retained in the result
    :param target: File to store the result in. Note that any previous contents
        will be deleted.
    """
    res = ""
    for file in file_paths:
        with open(file, "r") as f:
            res += f.read()
    with open(target, "w+") as f:
        f.write(res)


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

# Concatenate sections -> individual component examples -> multi-component examples

definition_sections = os.listdir(PATH_DOCS_PIPELINE_COMPONENTS / "sections")
pipeline_components = os.listdir(PATH_DOCS_PIPELINE_COMPONENTS / "headers")
pipeline_component_defaults = os.listdir(
    PATH_DOCS_RESOURCES / "pipeline-defaults/headers"
)

def sort_(to_be_ordered: list[str], ordering: list[str]):
    res = []
    for rule in ordering:
        for subject in to_be_ordered:
            if subject.startswith(rule + "-"):
                res.append(subject)
    return res

definition_sections = sort_(definition_sections, SECTIONS_ORDER)

for file in pipeline_components:
    component_name = file.removesuffix(".yaml")
    component_defaults_name = "defaults-" + file

    defaults_sections_paths = [
        PATH_DOCS_RESOURCES / "pipeline-defaults/headers" / component_defaults_name
    ] + [
        PATH_DOCS_PIPELINE_COMPONENTS / "sections" / section
        for section in definition_sections
        if component_name in section
    ]
    # Concatenate defaults sections into component-specific default files
    concatenate_text_files(
        *(defaults_sections_paths),
        target=PATH_DOCS_RESOURCES / "pipeline-defaults/" / component_defaults_name,
    )
# # kafka-connector is an edge case
# kafka_connector_sections = [
#     ""
# ]
# concatenate_text_files(
#     *()
# )

# Concatenate components into a full pipeline def
concatenate_text_files(
    *(
        PATH_DOCS_PIPELINE_COMPONENTS / s
        for s in pipeline_components
        if "kafka-connector" not in s
    ),
    target=PATH_DOCS_PIPELINE_COMPONENTS / "pipeline.yaml",
)
# Concatenate component-specific defaults into a full defaults file
concatenate_text_files(
    *(
        PATH_DOCS_RESOURCES / "pipeline-defaults" / s
        for s in pipeline_component_defaults
    ),
    target=PATH_DOCS_RESOURCES / "pipeline-defaults" / "defaults.yaml",
)
