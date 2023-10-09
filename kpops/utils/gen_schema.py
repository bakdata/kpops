import json
import logging
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import Field, TypeAdapter
from pydantic.json_schema import model_json_schema, models_json_schema
from pydantic_core import to_json

from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import _find_classes
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.docstring import describe_object


class SchemaScope(str, Enum):
    PIPELINE = "pipeline"
    CONFIG = "config"


log = logging.getLogger("")


def _is_valid_component(
    defined_component_types: set[str], component: type[PipelineComponent]
) -> bool:
    """
    Check whether a PipelineComponent subclass has a valid definition for the schema generation.

    :param defined_component_types: types defined so far
    :param component: component type to be validated
    :return: Whether component is valid for schema generation
    """
    if component.type in defined_component_types:
        log.warning(f"SKIPPED {component.__name__}, component type must be unique.")
        return False
    else:
        defined_component_types.add(component.type)
        return True


def _add_components(
    components_module: str,
    components: tuple[type[PipelineComponent], ...] | None = None,
) -> tuple[type[PipelineComponent], ...]:
    """Add components to a components tuple

    If an empty tuple is provided or it is not provided at all, the components
    types from the given module are 'tupled'

    :param components_module: Python module. Only the classes that inherit from
        PipelineComponent will be considered.
    :param components: Tuple of components to which to add, defaults to ()
    :return: Extended tuple
    """
    if components is None:
        components = tuple()
    # Set of existing types, against which to check the new ones
    defined_component_types = {component.type for component in components}
    custom_components = (
        component
        for component in _find_classes(components_module, PipelineComponent)
        if _is_valid_component(defined_component_types, component)
    )
    components += tuple(custom_components)
    return components


def gen_pipeline_schema(
    components_module: str | None = None, include_stock_components: bool = True
) -> None:
    """Generate a json schema from the models of pipeline components.

    :param components_module: Python module. Only the classes that inherit from
        PipelineComponent will be considered., defaults to None
    :param include_stock_components: Whether to include the stock components,
        defaults to True
    """
    if not (include_stock_components or components_module):
        log.warning("No components are provided, no schema is generated.")
        return
    # Add stock components if enabled
    components: tuple[type[PipelineComponent], ...] = tuple()
    if include_stock_components:
        components = tuple(_find_classes("kpops.components", PipelineComponent))
    # Add custom components if provided
    if components_module:
        components = _add_components(components_module, components)
    if not components:
        raise RuntimeError("No valid components found.")

    # re-assign component type as Literal to work as discriminator
    for component in components:
        component.model_fields["type"] = Field(
            alias="type",
            type_=Literal[component.type],  # type: ignore
            default=component.type,
            # final=True,
            title="Component type",
            description=describe_object(component.__doc__),
            # model_config=BaseConfig,
            # class_validators=None,
        )
    components_moded = tuple([(component, "serialization") for component in components])

    schema = models_json_schema(
        components_moded,
        title="KPOps pipeline schema",
        by_alias=True,
        ref_template="#/definitions/{model}",
    )
    # breakpoint()
    stripped_schema_first_item = {k[0]: v for k, v in schema[0].items()}
    schema_first_item_adapted = {
        "discriminator": {
            "mapping": {},
            "propertyName": "type",
        },
        "oneOf": [],
    }
    mapping = {}
    one_of = []
    for k, v in stripped_schema_first_item.items():
        mapping[k.type] = v["$ref"]
        one_of.append(v)
    schema_first_item_adapted["discriminator"]["mapping"] = mapping
    schema_first_item_adapted["oneOf"] = one_of
    complete_schema = schema[1].copy()
    complete_schema["items"] = schema_first_item_adapted
    complete_schema["type"] = "array"
    print(
        json.dumps(
            complete_schema,
            indent=4,
            sort_keys=True,
        )
    )

    # Create a type union that will hold the union of all component types
    # PipelineComponents = Union[components]  # type: ignore[valid-type]
    # AnnotatedPipelineComponents = Annotated[
    #     PipelineComponents, Field(discriminator="type")
    # ]
    # DumpablePipelineComponents = TypeAdapter(AnnotatedPipelineComponents)

    # schema = to_json(AnnotatedPipelineComponents)

    # print(schema)


def gen_config_schema() -> None:
    """Generate a json schema from the model of pipeline config"""
    schema = model_json_schema(PipelineConfig)
    print(json.dumps(schema, indent=4, sort_keys=True))
