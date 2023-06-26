"""Generates the whole 'generatable' KPOps documentation"""
import os
import subprocess
from enum import Enum
from multiprocessing import Value
from pathlib import Path
from pprint import pprint

from hooks import PATH_ROOT
from kpops.cli.registry import _find_classes
from kpops.components.base_components.pipeline_component import PipelineComponent

PATH_KPOPS_MAIN = PATH_ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = PATH_ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"
PATH_DOCS_PIPELINE_COMPONENTS = PATH_DOCS_RESOURCES / "pipeline-components"
KPOPS_COMPONENTS = tuple(_find_classes("kpops.components", PipelineComponent))
INHERITANCE_REF: dict = {
    component.get_component_type(): component.__base__.get_component_type()
    for component in KPOPS_COMPONENTS
}
COMPONENTS_FIELDS = {
    component.get_component_type(): component.__fields__.keys()
    for component in KPOPS_COMPONENTS
}


# SECTIONS_ORDER = [
#     "type",
#     "name",
#     "namespace",
#     "app",
#     "from",
#     "to",
#     "prefix",
#     "repo-config",
#     "version",
#     "resetter-values",
#     "offset-topic",
# ]

pprint(COMPONENTS_FIELDS)

#####################
# EXAMPLES          #
#####################

def get_sections(component_name: str, sections: list[str]) -> list[str]:
    """Find all sections that apply to a component from a list

    :param component_name: Component name
    :param sections: Available section files, names with extension, no path
    :returns: The applicable sections
    """
    component_sections: list[str] = []
    for target_section in COMPONENTS_FIELDS[component_name]:
        if (section := target_section + "-" + component_name + ".yaml") in sections:
            component_sections.append(section)
    return component_sections


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


# Concatenate sections -> individual component examples -> multi-component examples

# Collect file names
definition_sections = os.listdir(PATH_DOCS_PIPELINE_COMPONENTS / "sections")
pipeline_components = os.listdir(PATH_DOCS_PIPELINE_COMPONENTS / "headers")
pipeline_component_defaults = os.listdir(
    PATH_DOCS_RESOURCES / "pipeline-defaults/headers"
)


# def sort_(to_be_ordered: list[str], ordering: list[str]):
#     res = []
#     for rule in ordering:
#         for subject in to_be_ordered:
#             if subject.startswith(rule + "-"):
#                 res.append(subject)
#     return res


for file in pipeline_components:
    component_name = file.removesuffix(".yaml")
    component_defaults_name = "defaults-" + file
    # component_sections = sort_(definition_sections, COMPONENTS_FIELDS[component_name])
    sections = get_sections(component_name, definition_sections)
    defaults_sections_paths = [
        PATH_DOCS_RESOURCES / "pipeline-defaults/headers" / component_defaults_name
    ] + [PATH_DOCS_PIPELINE_COMPONENTS / "sections" / section for section in sections]
    # Concatenate defaults sections into component-specific default files
    concatenate_text_files(
        *(defaults_sections_paths),
        target=PATH_DOCS_RESOURCES / "pipeline-defaults/" / component_defaults_name,
    )

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
