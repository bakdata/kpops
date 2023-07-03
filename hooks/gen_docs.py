"""Generates the whole 'generatable' KPOps documentation"""
import os
import subprocess
from pathlib import Path

import yaml

from hooks import PATH_ROOT
from kpops.cli.registry import _find_classes
from kpops.components.base_components.pipeline_component import PipelineComponent
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
KPOPS_COMPONENTS_INHERITANCE_REF: dict = {
    component.get_component_type(): component.__base__.get_component_type()  # type: ignore[reportGeneralTypeIssues]
    for component in KPOPS_COMPONENTS
}
KPOPS_COMPONENTS_FIELDS = {
    # `set` to make it pickleable
    component.get_component_type(): set(component.__fields__.keys())
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
    for target_section in KPOPS_COMPONENTS_FIELDS[component_name]:
        component = component_name
        section = target_section + "-" + component + ".yaml"
        if section in sections:
            component_sections.append(section)
        elif (
            not include_inherited
            and KPOPS_COMPONENTS_INHERITANCE_REF[component] == "pipeline-component"
        ):
            section = target_section + ".yaml"
            if section in sections:
                component_sections.append(section)
        elif include_inherited:
            while component != "pipeline-component":
                component = KPOPS_COMPONENTS_INHERITANCE_REF[component]
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
    """Concatenate the given files into one

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
    :returns: The corresponding position or 0 if not found
    """
    for section in SECTIONS_ORDER:
        if key.startswith((section + "-", section + ".")):
            return SECTIONS_ORDER.index(section)
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
        "kpops_components_fields": KPOPS_COMPONENTS_FIELDS,
    }
    if kpops_new_structure != kpops_structure:
        with open(PATH_DOCS_KPOPS_STRUCTURE, "w+") as f:
            yaml.dump(kpops_new_structure, f)
        with open(PATH_DOCS_COMPONENTS_DEPENDENCIES, "w+"):
            pass
        with open(PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS, "w+"):
            pass
        print("KPOps components' structure has changed, updating dependencies.")
        return True
    return False


def get_sections(exist_changes: bool) -> tuple[list[str], list[str]]:
    """Returns the sections specific to a component

    :param exist_changes: Whether there have been changes to the components
        structure or hierarchy
    :returns: A tuple containing lists of all sections and defaults-related sections
    """
    if exist_changes:
        component_sections = filter_sections(
            component_name, components_definition_sections, True
        )
        component_sections_not_inheritted = filter_sections(
            component_name, components_definition_sections
        )
        with open(
            PATH_DOCS_COMPONENTS_DEPENDENCIES,
            "a",
        ) as f:
            yaml.dump({component_file_name: component_sections}, f)
        with open(
            PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS,
            "a",
        ) as f:
            yaml.dump({component_file_name: component_sections_not_inheritted}, f)
    else:
        component_sections: list[str] = pipeline_component_dependencies[
            component_file_name
        ]
        component_sections_not_inheritted: list[
            str
        ] = defaults_pipeline_component_dependencies[component_file_name]
    return component_sections, component_sections_not_inheritted


components_definition_sections = os.listdir(PATH_DOCS_COMPONENTS / "sections")
pipeline_component_file_names = os.listdir(PATH_DOCS_COMPONENTS / "headers")
pipeline_component_file_names.sort()
pipeline_component_defaults = os.listdir(
    PATH_DOCS_RESOURCES / "pipeline-defaults/headers"
)
pipeline_component_defaults.sort()
is_change_present = check_for_changes_in_kpops_component_structure()

try:
    pipeline_component_dependencies_temp = load_yaml_file(
        PATH_DOCS_COMPONENTS_DEPENDENCIES
    )
    defaults_pipeline_component_dependencies_temp = load_yaml_file(
        PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS
    )
    assert isinstance(pipeline_component_dependencies_temp, dict)
    assert isinstance(defaults_pipeline_component_dependencies_temp, dict)
    # HACK: Otherwise pyright cannot see that the type is narrowed right after initializing the vars
    pipeline_component_dependencies: dict = pipeline_component_dependencies_temp
    defaults_pipeline_component_dependencies: dict = (
        defaults_pipeline_component_dependencies_temp
    )
except OSError:
    is_change_present = True
except AssertionError:
    raise TypeError(
        f"The following files must be a mapping: \n{PATH_DOCS_COMPONENTS_DEPENDENCIES}\n{PATH_DOCS_COMPONENTS_DEPENDENCIES_DEFAULTS}"
    )


for component_file_name in pipeline_component_file_names:
    component_name = component_file_name.removesuffix(".yaml")
    component_defaults_name = "defaults-" + component_file_name

    component_sections, component_sections_not_inheritted = get_sections(
        is_change_present
    )

    defaults_sections_paths = [
        PATH_DOCS_RESOURCES / "pipeline-defaults/headers" / component_defaults_name
    ] + [
        PATH_DOCS_COMPONENTS / "sections" / section
        for section in component_sections_not_inheritted
    ]
    sections_paths = [
        PATH_DOCS_RESOURCES / "pipeline-components/headers" / component_file_name
    ] + [PATH_DOCS_COMPONENTS / "sections" / section for section in component_sections]
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
        PATH_DOCS_COMPONENTS / component
        for component in pipeline_component_file_names
        if "kafka-connector" not in component  # Shouldn't be used in the pipeline def
    ),
    target=PATH_DOCS_COMPONENTS / "pipeline.yaml",
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
