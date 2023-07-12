"""Generates the whole 'generatable' KPOps documentation"""
import logging
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, cast

import yaml

from hooks import PATH_ROOT
from kpops.cli.registry import _find_classes
from kpops.components import KafkaConnector, PipelineComponent
from kpops.components.base_components.base_defaults_component import deduplicate
from kpops.utils.colorify import redify, yellowify
from kpops.utils.yaml_loading import load_yaml_file

PATH_KPOPS_MAIN = PATH_ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = PATH_ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"
PATH_DOCS_COMPONENTS = PATH_DOCS_RESOURCES / "pipeline-components"
PATH_DOCS_COMPONENTS_DEPENDENCIES = (
    PATH_DOCS_COMPONENTS / "dependencies/pipeline_component_dependencies.yaml"
)
PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS = (
    PATH_DOCS_COMPONENTS / "dependencies/defaults_pipeline_component_dependencies.yaml"
)
PATH_DOCS_KPOPS_STRUCTURE = PATH_DOCS_COMPONENTS / "dependencies/kpops_structure.yaml"
KPOPS_COMPONENTS = tuple(_find_classes("kpops.components", PipelineComponent))
KPOPS_COMPONENTS_INHERITANCE_REF = {
    component.get_component_type(): cast(
        type[PipelineComponent], component.__base__
    ).get_component_type()
    for component in KPOPS_COMPONENTS
}
KPOPS_COMPONENTS_SECTIONS = {
    component.get_component_type(): [
        field_name
        for field_name, model in component.__fields__.items()
        if not model.field_info.exclude
    ]
    for component in KPOPS_COMPONENTS
}
KPOPS_COMPONENTS_SECTIONS_ORDER = deduplicate(
    [field for fields in KPOPS_COMPONENTS_SECTIONS.values() for field in fields]
)

log = logging.getLogger("DocumentationGenerator")

#####################
# EXAMPLES          #
#####################

DANGEROUS_FILES_TO_CHANGE = {
    PATH_DOCS_COMPONENTS_DEPENDENCIES,
    PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS,
    PATH_DOCS_KPOPS_STRUCTURE,
}
# All args provided to the script
# Pre-commit passes changed files as args
SCRIPT_ARGUMENTS = set(sys.argv)
# Dependency files should not be changed manually
# Set `is_change_present` to indicate that dependencies need to be regenerated
# and delete the old dependency files
if not {
    str(file.relative_to(PATH_ROOT)) for file in DANGEROUS_FILES_TO_CHANGE
}.isdisjoint(SCRIPT_ARGUMENTS):
    is_change_present = True
    for dangerous_file in DANGEROUS_FILES_TO_CHANGE:
        dangerous_file.unlink(missing_ok=True)
    # Don't display warning if `-a` flag suspected in `pre-commit run`
    if ".gitignore" not in SCRIPT_ARGUMENTS:
        log.warning(
            redify(
                "\nPossible changes in the dependency dir detected."
                " It should not be edited in any way manually."
                "\nTO RESET, DELETE THE DEPENDENCY DIR MANUALLY\n"
            )
        )
else:
    is_change_present = False

COMPONENTS_DEFINITION_SECTIONS = list((PATH_DOCS_COMPONENTS / "sections").iterdir())
PIPELINE_COMPONENT_HEADER_FILES = sorted(
    list((PATH_DOCS_COMPONENTS / "headers").iterdir())
)
PIPELINE_COMPONENT_DEFAULTS_HEADER_FILES = sorted(
    list((PATH_DOCS_RESOURCES / "pipeline-defaults/headers").iterdir())
)


class KpopsComponent(NamedTuple):
    attrs: list[str]
    specific_attrs: list[str]


def filter_sections(
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
    for target_section in KPOPS_COMPONENTS_SECTIONS[component_name]:
        if section := filter_section(component_name, sections, target_section):
            component_sections.append(section)
        elif include_inherited:
            temp_component_name = component_name
            while (
                temp_component_name := KPOPS_COMPONENTS_INHERITANCE_REF[
                    temp_component_name
                ]
            ) != PipelineComponent.get_component_type():
                if section := filter_section(
                    temp_component_name, sections, target_section
                ):
                    component_sections.append(section)
                    break
    component_sections.sort(key=component_section_position_in_definition)
    return component_sections


def filter_section(
    component_name: str, sections: list[str], target_section: str
) -> str | None:
    """Find target section that is specific to a component from a list

    :param component_name: Component name
    :param sections: Available section files, names with extension, no path
    :param target_section: Section to look for
    :returns: The applicable section or None if no section found
    """
    section = target_section + "-" + component_name + ".yaml"
    if section in sections:
        return section
    elif (
        KPOPS_COMPONENTS_INHERITANCE_REF[component_name]
        == PipelineComponent.get_component_type()
    ):
        section = target_section + ".yaml"
        if section in sections:
            return section


def concatenate_text_files(*sources: Path, target: Path) -> None:
    """Concatenate the given files into one

    :param *sources: Files to be conatenated. The order of the inputs will be
        retained in the result
    :param target: File to store the result in. Note that any previous contents
        will be deleted.
    """
    with target.open("w+") as f:
        for source in sources:
            f.write(source.read_text())
    log.debug(f"Successfully generated {target}")


def component_section_position_in_definition(key: str) -> int:
    """Returns a positional value for a given str if found in the list of
    component definition sections

    :param key: A value to look for in the list of sections
    :returns: The corresponding position or 0 if not found
    """
    for section in KPOPS_COMPONENTS_SECTIONS_ORDER:
        if key.startswith((section + "-", section + ".")):
            return KPOPS_COMPONENTS_SECTIONS_ORDER.index(section)
    return 0


def check_for_changes_in_kpops_component_structure() -> bool:
    """Detect changes in the hierarchy or the structure of KPOps' components

    If a change is detected, a new structure yaml is written and the dependency
    reference yamls are emptied.
    Also prints a message if changes are detected.

    :returns: True if change is found
    """
    try:
        kpops_structure = load_yaml_file(PATH_DOCS_KPOPS_STRUCTURE)
    except OSError:
        kpops_structure = None
    kpops_new_structure = {
        "kpops_components_inheritance_ref": KPOPS_COMPONENTS_INHERITANCE_REF,
        "kpops_components_fields": KPOPS_COMPONENTS_SECTIONS,
    }
    if kpops_new_structure != kpops_structure:
        (PATH_DOCS_COMPONENTS / "dependencies").mkdir(parents=True, exist_ok=True)
        with PATH_DOCS_KPOPS_STRUCTURE.open("w+") as f:
            yaml.dump(kpops_new_structure, f)
        PATH_DOCS_COMPONENTS_DEPENDENCIES.unlink(missing_ok=True)
        PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS.unlink(missing_ok=True)
        if ".gitignore" not in SCRIPT_ARGUMENTS:
            log.warning(
                yellowify(
                    "\nKPOps components' structure has likely changed, updating dependencies."
                    "\nIn case you didn't change the structure, make sure that you didn't"
                    " manually introduce changes in the dependency dir.\n"
                )
            )
        else:
            log.debug("Dependency files updated.")
        return True
    return False


def get_sections(component_name: str, exist_changes: bool) -> KpopsComponent:
    """Returns the sections specific to a component

    :param exist_changes: Whether there have been changes to the components
        structure or hierarchy
    :returns: A tuple containing lists of all sections and defaults-related sections
    """
    component_definition_sections_names = [
        section.name for section in COMPONENTS_DEFINITION_SECTIONS
    ]
    component_file_name = component_name + ".yaml"
    if exist_changes:
        component_sections = filter_sections(
            component_name, component_definition_sections_names, True
        )
        component_sections_not_inherited = filter_sections(
            component_name, component_definition_sections_names
        )
        with PATH_DOCS_COMPONENTS_DEPENDENCIES.open("a") as f:
            yaml.dump({component_file_name: component_sections}, f)
        with PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS.open("a") as f:
            yaml.dump({component_file_name: component_sections_not_inherited}, f)
    else:
        component_sections: list[str] = PIPELINE_COMPONENT_DEPENDENCIES[  # type: ignore [reportGeneralTypeIssues]
            component_file_name
        ]
        component_sections_not_inherited: list[
            str
        ] = DEFAULTS_PIPELINE_COMPONENT_DEPENDENCIES[  # type: ignore [reportGeneralTypeIssues]
            component_file_name
        ]
    return KpopsComponent(component_sections, component_sections_not_inherited)


is_change_present = (
    check_for_changes_in_kpops_component_structure() or is_change_present
)

try:
    PIPELINE_COMPONENT_DEPENDENCIES = load_yaml_file(PATH_DOCS_COMPONENTS_DEPENDENCIES)
    DEFAULTS_PIPELINE_COMPONENT_DEPENDENCIES = load_yaml_file(
        PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS
    )
except OSError:
    is_change_present = True

for component_file in PIPELINE_COMPONENT_HEADER_FILES:
    component_file_name = component_file.name
    component_type = component_file.stem
    component_defaults_name = "defaults-" + component_file_name

    component_sections, component_sections_not_inheritted = get_sections(
        component_type,
        is_change_present,
    )

    defaults_sections_paths = [
        PATH_DOCS_RESOURCES / "pipeline-defaults/headers" / component_defaults_name
    ] + [
        PATH_DOCS_COMPONENTS / "sections" / section
        for section in component_sections_not_inheritted
    ]
    sections_paths = [component_file] + [
        PATH_DOCS_COMPONENTS / "sections" / section for section in component_sections
    ]
    concatenate_text_files(
        *(defaults_sections_paths),
        target=PATH_DOCS_RESOURCES / "pipeline-defaults/" / component_defaults_name,
    )
    concatenate_text_files(
        *(sections_paths),
        target=PATH_DOCS_RESOURCES / "pipeline-components" / component_file_name,
    )
concatenate_text_files(
    *(
        component_file.parents[1] / component_file.name
        for component_file in PIPELINE_COMPONENT_HEADER_FILES
        if KafkaConnector.get_component_type()
        != component_file.stem  # Shouldn't be used in the pipeline def
    ),
    target=PATH_DOCS_COMPONENTS / "pipeline.yaml",
)
concatenate_text_files(
    *(
        component.parents[1] / component.name
        for component in PIPELINE_COMPONENT_DEFAULTS_HEADER_FILES
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
