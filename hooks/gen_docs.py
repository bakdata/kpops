"""Generates the whole 'generatable' KPOps documentation"""
import os
import subprocess
from pathlib import Path

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
SECTIONS_ORDER = [
    "type",
    "name",
    "namespace",
    "app",
    "from_",
    "to",
    "prefix",
    "repo_config",
    "version",
    "resetter_values",
    "offset_topic",
]

#####################
# EXAMPLES          #
#####################


def get_sections(
    component_name: str, sections: list[str], include_inherited: bool = False
) -> list[str]:
    """Find all sections that are specific to a component from a list

    :param component_name: Component name
    :param sections: Available section files, names with extension, no path
    :param include_inherited: Whether to include sections that can be defined in
        a parent component defaults
    :returns: The applicable sections
    """
    component_sections: list[str] = []
    for target_section in COMPONENTS_FIELDS[component_name]:
        component = component_name
        section = target_section + "-" + component + ".yaml"
        if section in sections:
            component_sections.append(section)
        elif (
            not include_inherited and INHERITANCE_REF[component] == "pipeline-component"
        ):
            section = target_section + ".yaml"
            if section in sections:
                component_sections.append(section)
        elif include_inherited:
            while component != "pipeline-component":
                component = INHERITANCE_REF[component]
                section = target_section + "-" + component + ".yaml"
                if section in sections:
                    component_sections.append(section)
                    break
                elif component == "pipeline-component":
                    section = target_section + ".yaml"
                    if section in sections:
                        component_sections.append(section)
                        break
    component_sections.sort(key=component_section_position_in_definition)
    return component_sections


def concatenate_text_files(*file_paths: Path, target: Path) -> None:
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


def component_section_position_in_definition(key: str) -> int:
    """Returns a positional value for a given str if found in the list of
    component definition sections

    :param key: A value to look for in the list of sections
    :return: The corresponding position or 0 if not found
    """
    for section in SECTIONS_ORDER:
        if key.startswith((section + "-", section + ".")):
            return SECTIONS_ORDER.index(section)
    return 0


components_definition_sections = os.listdir(PATH_DOCS_PIPELINE_COMPONENTS / "sections")
pipeline_component_file_names = os.listdir(PATH_DOCS_PIPELINE_COMPONENTS / "headers")
pipeline_component_defaults = os.listdir(
    PATH_DOCS_RESOURCES / "pipeline-defaults/headers"
)


for component_file_name in pipeline_component_file_names:
    component_name = component_file_name.removesuffix(".yaml")
    component_defaults_name = "defaults-" + component_file_name
    component_sections = get_sections(
        component_name, components_definition_sections, True
    )
    component_sections_not_inheritted = get_sections(
        component_name, components_definition_sections
    )

    defaults_sections_paths = [
        PATH_DOCS_RESOURCES / "pipeline-defaults/headers" / component_defaults_name
    ] + [
        PATH_DOCS_PIPELINE_COMPONENTS / "sections" / section
        for section in component_sections_not_inheritted
    ]
    sections_paths = [
        PATH_DOCS_RESOURCES / "pipeline-components/headers" / component_file_name
    ] + [
        PATH_DOCS_PIPELINE_COMPONENTS / "sections" / section
        for section in component_sections
    ]
    concatenate_text_files(
        *(defaults_sections_paths),
        target=PATH_DOCS_RESOURCES / "pipeline-defaults/" / component_defaults_name,
    )
    concatenate_text_files(
        *(sections_paths),
        target=PATH_DOCS_RESOURCES / "pipeline-components/" / component_file_name,
    )

concatenate_text_files(
    *(
        PATH_DOCS_PIPELINE_COMPONENTS / component
        for component in pipeline_component_file_names
        if "kafka-connector" not in component  # Shouldn't be used in the pipeline def
    ),
    target=PATH_DOCS_PIPELINE_COMPONENTS / "pipeline.yaml",
)
concatenate_text_files(
    *(
        PATH_DOCS_RESOURCES / "pipeline-defaults" / component
        for component in pipeline_component_defaults
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
