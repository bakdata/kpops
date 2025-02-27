"""Generates pipeline definition examples from manually written building blocks."""

import logging
import sys
from pathlib import Path
from typing import NamedTuple, cast

import yaml

from hooks import ROOT
from kpops.components.base_components.kafka_connector import KafkaConnector
from kpops.components.base_components.pipeline_component import (
    PipelineComponent,
)
from kpops.core.registry import Registry
from kpops.utils.colorify import redify, yellowify
from kpops.utils.pydantic import issubclass_patched
from kpops.utils.yaml import load_yaml_file

registry = Registry()
registry.discover_components()

PATH_KPOPS_MAIN = ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = ROOT / "docs/docs/resources"
PATH_DOCS_COMPONENTS = PATH_DOCS_RESOURCES / "pipeline-components"
PATH_DOCS_COMPONENTS_DEPENDENCIES = (
    PATH_DOCS_COMPONENTS / "dependencies/pipeline_component_dependencies.yaml"
)
PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS = (
    PATH_DOCS_COMPONENTS / "dependencies/defaults_pipeline_component_dependencies.yaml"
)
PATH_DOCS_KPOPS_STRUCTURE = PATH_DOCS_COMPONENTS / "dependencies/kpops_structure.yaml"

# Paths to all manually maintained examples
COMPONENTS_DEFINITION_SECTIONS = list((PATH_DOCS_COMPONENTS / "sections").iterdir())
PIPELINE_COMPONENT_HEADER_FILES = sorted((PATH_DOCS_COMPONENTS / "headers").iterdir())
PIPELINE_COMPONENT_DEFAULTS_HEADER_FILES = sorted(
    (PATH_DOCS_RESOURCES / "pipeline-defaults/headers").iterdir(),
)

KPOPS_COMPONENTS = tuple(registry.components)
KPOPS_COMPONENTS_SECTIONS = {
    component.type: [
        field_name
        for field_name, field_info in component.model_fields.items()
        if not field_info.exclude
    ]
    for component in KPOPS_COMPONENTS
}
KPOPS_COMPONENTS_INHERITANCE_REF = {
    component.type: {
        "bases": [
            cast(
                type[PipelineComponent],
                base,
            ).type
            for base in component.__bases__
            if issubclass_patched(base, PipelineComponent)
        ],
        "parents": [
            cast(
                type[PipelineComponent],
                parent,
            ).type
            for parent in component.parents
        ],
    }
    for component in KPOPS_COMPONENTS
}

# Dependency files should not be changed manually
DANGEROUS_FILES_TO_CHANGE = {
    PATH_DOCS_COMPONENTS_DEPENDENCIES,
    PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS,
    PATH_DOCS_KPOPS_STRUCTURE,
}
# All args provided to the script
# pre-commit/lefthook pass changed files as args
SCRIPT_ARGUMENTS = set(sys.argv)

log = logging.getLogger("DocumentationGenerator")


class KpopsComponent(NamedTuple):
    """Stores the names of components fields.

    :param attrs: All fields
    :param specific_attrs: Fields that are NOT inherited
    """

    attrs: list[str]
    specific_attrs: list[str]


def filter_sections(
    component_name: str,
    sections: list[str],
    *,
    include_inherited: bool = False,
) -> list[str]:
    """Find all sections that are specific to a component from a list.

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
            for component in KPOPS_COMPONENTS_INHERITANCE_REF[component_name][
                "parents"
            ]:
                if component == PipelineComponent.type:
                    break
                if section := filter_section(
                    component,
                    sections,
                    target_section,
                ):
                    component_sections.append(section)
                    break
    return component_sections


def filter_section(
    component_name: str,
    sections: list[str],
    target_section: str,
) -> str | None:
    """Find target section that is specific to a component from a list.

    :param component_name: Component name
    :param sections: Available section files, names with extension, no path
    :param target_section: Section to look for
    :returns: The applicable section or None if no section found
    """
    section = target_section + "-" + component_name + ".yaml"
    if section in sections:
        return section
    if KPOPS_COMPONENTS_INHERITANCE_REF[component_name]["bases"] == [
        PipelineComponent.type
    ]:
        section = target_section + ".yaml"
        if section in sections:
            return section
    return None


def concatenate_text_files(*sources: Path, target: Path) -> None:
    """Concatenate the given files into one.

    :param *sources: Files to be conatenated. The order of the inputs will be
        retained in the result
    :param target: File to store the result in. Note that any previous contents
        will be deleted.
    """
    with target.open("w+") as f:
        for source in sources:
            f.write(source.read_text())
    log.debug("Successfully generated %s", target)


def check_for_changes_in_kpops_component_structure() -> bool:
    """Detect changes in the hierarchy or the structure of KPOps' components.

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
            yaml.safe_dump(kpops_new_structure, f)
        PATH_DOCS_COMPONENTS_DEPENDENCIES.unlink(missing_ok=True)
        PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS.unlink(missing_ok=True)
        if ".gitignore" not in SCRIPT_ARGUMENTS:
            log.warning(
                yellowify(
                    "\nKPOps components' structure has likely changed, updating dependencies."
                    "\nIn case you didn't change the structure, make sure that you didn't"
                    " manually introduce changes in the dependency dir.\n",
                ),
            )
        else:
            log.debug("Dependency files updated.")
        return True
    return False


def get_sections(component_name: str, *, exist_changes: bool) -> KpopsComponent:
    """Return the sections specific to a component.

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
            component_name,
            component_definition_sections_names,
            include_inherited=True,
        )
        component_sections_not_inherited = filter_sections(
            component_name,
            component_definition_sections_names,
        )
        with PATH_DOCS_COMPONENTS_DEPENDENCIES.open("a") as f:
            yaml.safe_dump({component_file_name: component_sections}, f)
        with PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS.open("a") as f:
            yaml.safe_dump({component_file_name: component_sections_not_inherited}, f)
    else:
        component_sections = PIPELINE_COMPONENT_DEPENDENCIES[component_file_name]
        component_sections_not_inherited = DEFAULTS_PIPELINE_COMPONENT_DEPENDENCIES[
            component_file_name
        ]
    return KpopsComponent(component_sections, component_sections_not_inherited)


if __name__ == "__main__":
    # Check if the dependencies have been modified
    if not {
        str(file.relative_to(ROOT)) for file in DANGEROUS_FILES_TO_CHANGE
    }.isdisjoint(SCRIPT_ARGUMENTS):
        # Set `is_change_present` to indicate that dependencies need to be regenerated
        is_change_present = True
        # Delete the old dependency files
        for dangerous_file in DANGEROUS_FILES_TO_CHANGE:
            dangerous_file.unlink(missing_ok=True)
        # Don't display warning if `--all-files` flag suspected in `pre-commit run` or `lefthook run`
        if ".gitignore" not in SCRIPT_ARGUMENTS:
            log.warning(
                redify(
                    "\nPossible changes in the dependency dir detected."
                    " It should not be edited in any way manually."
                    "\nTO RESET, DELETE THE DEPENDENCY DIR MANUALLY\n",
                ),
            )
    else:
        is_change_present = False

    # Always check for changes in the component structure, but even
    # if none found, True if the dependency files have been modified.
    is_change_present = (
        check_for_changes_in_kpops_component_structure() or is_change_present
    )

    # If some or all of dependencies cannot be loaded, likely relevant changes are present
    try:
        PIPELINE_COMPONENT_DEPENDENCIES: dict[str, list[str]] = load_yaml_file(
            PATH_DOCS_COMPONENTS_DEPENDENCIES
        )
        DEFAULTS_PIPELINE_COMPONENT_DEPENDENCIES: dict[str, list[str]] = load_yaml_file(
            PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS,
        )
    except OSError:
        is_change_present = True

    # For each component, use the section files to build an example
    # pipeline.yaml and defaults.yaml
    for component_file in PIPELINE_COMPONENT_HEADER_FILES:
        component_defaults_name = f"defaults-{component_file.name}"
        # Component-specific sections for pipeline def and defaults
        component_sections, component_sections_not_inherited = get_sections(
            component_file.stem,
            exist_changes=is_change_present,
        )

        defaults_sections_paths = [
            PATH_DOCS_RESOURCES / "pipeline-defaults/headers" / component_defaults_name,
        ] + [
            PATH_DOCS_COMPONENTS / "sections" / section
            for section in component_sections_not_inherited
        ]
        sections_paths = [component_file] + [
            PATH_DOCS_COMPONENTS / "sections" / section
            for section in component_sections
        ]
        concatenate_text_files(
            *(defaults_sections_paths),
            target=PATH_DOCS_RESOURCES / "pipeline-defaults/" / component_defaults_name,
        )
        concatenate_text_files(
            *(sections_paths),
            target=PATH_DOCS_RESOURCES / "pipeline-components" / component_file.name,
        )
    # Concatenate all component-specific pipeline definitions into 1 complete pipeline.yaml
    concatenate_text_files(
        *(
            component_file.parents[1] / component_file.name
            for component_file in PIPELINE_COMPONENT_HEADER_FILES
            if component_file.stem
            != KafkaConnector.type  # shouldn't be used in the pipeline def
        ),
        target=PATH_DOCS_COMPONENTS / "pipeline.yaml",
    )
    # Concatenate all component-specific defaults into 1 complete defaults.yaml
    concatenate_text_files(
        *(
            component.parents[1] / component.name
            for component in PIPELINE_COMPONENT_DEFAULTS_HEADER_FILES
        ),
        target=PATH_DOCS_RESOURCES / "pipeline-defaults" / "defaults.yaml",
    )
