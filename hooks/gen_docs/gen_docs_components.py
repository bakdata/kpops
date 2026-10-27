"""Generates pipeline definition examples from manually written building blocks."""

import inspect
from abc import ABC
from pathlib import Path
from typing import cast

import structlog
import yaml

from hooks import ROOT
from kpops.components.base_components.base_defaults_component import (
    is_component_type,
)
from kpops.components.base_components.kafka_app import (
    ConsumesTopics,
    ProducesTopics,
)
from kpops.components.base_components.kafka_connector import KafkaConnector
from kpops.components.base_components.pipeline_component import (
    PipelineComponent,
)
from kpops.core.registry import Registry

registry = Registry()
registry.discover_components()


def generic_origin(component: type[PipelineComponent]) -> type[PipelineComponent]:
    """Map a parametrized generic component class to its unparametrized origin."""
    origin = component.__pydantic_generic_metadata__["origin"]
    if origin is not None and issubclass(origin, PipelineComponent):
        return origin
    return component


def component_bases(
    component: type[PipelineComponent],
) -> list[type[PipelineComponent]]:
    """Resolve the direct component bases of a component.

    Parametrized generics are mapped to their origin and capability classes are
    replaced by their own bases. The result is deduplicated and ordered.
    """
    bases: list[type[PipelineComponent]] = []
    for base in component.__bases__:
        if not issubclass(base, PipelineComponent):
            continue
        base = generic_origin(base)
        resolved = [base] if is_component_type(base) else component_bases(base)
        bases.extend(b for b in resolved if b not in bases)
    return bases


CAPABILITY_FIELDS: dict[type[PipelineComponent], tuple[str, ...]] = {
    ConsumesTopics: ("from_",),
    ProducesTopics: ("to",),
}


def has_direct_capability_field(
    component: type[PipelineComponent], field_name: str
) -> bool:
    """Whether a capability that declares the field is a direct base of the component."""
    return any(
        generic_origin(base) in CAPABILITY_FIELDS
        and field_name in CAPABILITY_FIELDS[generic_origin(base)]
        for base in component.__bases__
        if issubclass(base, PipelineComponent)
    )


PATH_DOCS_RESOURCES = ROOT / "docs/docs/resources"

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
        "bases": [base.type for base in component_bases(component)],
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

log = structlog.get_logger("DocumentationGenerator")


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
    if has_direct_capability_field(registry[component_name], target_section):
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
    log.debug("Successfully generated file", target=target)


def defaults_header_name(component_type: str) -> str:
    """Return the file name of the ``defaults.yaml`` header of a component."""
    return f"defaults-{component_type}.yaml"


def check_templates(docs_resources: Path = PATH_DOCS_RESOURCES) -> None:
    """Fail if a concrete component lacks its documentation headers."""
    missing: list[Path] = []
    for component in KPOPS_COMPONENTS:
        if inspect.isabstract(component) or ABC in component.__bases__:
            continue
        missing.extend(
            path.relative_to(docs_resources)
            for path in (
                docs_resources
                / "pipeline-components/headers"
                / f"{component.type}.yaml",
                docs_resources
                / "pipeline-defaults/headers"
                / defaults_header_name(component.type),
            )
            if not path.exists()
        )
    if missing:
        msg = "Missing documentation templates:\n" + "\n".join(
            str(path) for path in missing
        )
        raise SystemExit(msg)


def dump_yaml(path: Path, data: object) -> None:
    """Write ``data`` as YAML, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data))


def main(docs_resources: Path = PATH_DOCS_RESOURCES) -> None:
    """Generate the example definitions below ``docs_resources``."""
    check_templates(docs_resources)

    components_dir = docs_resources / "pipeline-components"
    defaults_dir = docs_resources / "pipeline-defaults"
    section_names = [
        section.name for section in (components_dir / "sections").iterdir()
    ]
    component_files = sorted((components_dir / "headers").iterdir())
    defaults_files = sorted((defaults_dir / "headers").iterdir())
    component_types = [file.stem for file in component_files]
    unknown = sorted(set(component_types) - set(KPOPS_COMPONENTS_SECTIONS))
    if unknown:
        msg = f"Header files without a matching KPOps component: {unknown}"
        raise SystemExit(msg)

    components_sections = {
        f"{name}.yaml": filter_sections(name, section_names, include_inherited=True)
        for name in component_types
    }
    defaults_sections = {
        f"{name}.yaml": filter_sections(name, section_names) for name in component_types
    }
    dump_yaml(
        components_dir / "dependencies/kpops_structure.yaml",
        {
            "kpops_components_inheritance_ref": KPOPS_COMPONENTS_INHERITANCE_REF,
            "kpops_components_fields": KPOPS_COMPONENTS_SECTIONS,
        },
    )
    dump_yaml(
        components_dir / "dependencies/pipeline_component_dependencies.yaml",
        components_sections,
    )
    dump_yaml(
        components_dir / "dependencies/defaults_pipeline_component_dependencies.yaml",
        defaults_sections,
    )

    for component_file in component_files:
        defaults_name = defaults_header_name(component_file.stem)
        concatenate_text_files(
            defaults_dir / "headers" / defaults_name,
            *(
                components_dir / "sections" / section
                for section in defaults_sections[component_file.name]
            ),
            target=defaults_dir / defaults_name,
        )
        concatenate_text_files(
            component_file,
            *(
                components_dir / "sections" / section
                for section in components_sections[component_file.name]
            ),
            target=components_dir / component_file.name,
        )
    # Concatenate all component-specific pipeline definitions into 1 complete pipeline.yaml
    concatenate_text_files(
        *(
            components_dir / component_file.name
            for component_file in component_files
            if component_file.stem
            != KafkaConnector.type  # shouldn't be used in the pipeline def
        ),
        target=components_dir / "pipeline.yaml",
    )
    # Concatenate all component-specific defaults into 1 complete defaults.yaml
    concatenate_text_files(
        *(defaults_dir / file.name for file in defaults_files),
        target=defaults_dir / "defaults.yaml",
    )


if __name__ == "__main__":
    main()
