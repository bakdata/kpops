import inspect
import json
import logging
from abc import ABC
from collections.abc import Sequence
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from pydantic.json_schema import GenerateJsonSchema, model_json_schema

from kpops.cli.registry import _find_classes
from kpops.components import PipelineComponent
from kpops.config import KpopsConfig


class SchemaScope(str, Enum):
    PIPELINE = "pipeline"
    CONFIG = "config"


class MultiComponentGenerateJsonSchema(GenerateJsonSchema):
    ...


log = logging.getLogger("")


def _is_valid_component(
    defined_component_types: set[str], component: type[PipelineComponent]
) -> bool:
    """Check whether a PipelineComponent subclass has a valid definition for the schema generation.

    :param defined_component_types: types defined so far
    :param component: component type to be validated
    :return: Whether component is valid for schema generation
    """
    if inspect.isabstract(component) or ABC in component.__bases__:
        log.warning(f"SKIPPED {component.__name__}, component is abstract.")
        return False
    if component.type in defined_component_types:
        log.warning(f"SKIPPED {component.__name__}, component type must be unique.")
        return False
    defined_component_types.add(component.type)
    return True


def _add_components(
    components_module: str,
    components: tuple[type[PipelineComponent], ...] | None = None,
) -> tuple[type[PipelineComponent], ...]:
    """Add components to a components tuple.

    If an empty tuple is provided or it is not provided at all, the components
    types from the given module are 'tupled'

    :param components_module: Python module. Only the classes that inherit from
        PipelineComponent will be considered.
    :param components: Tuple of components to which to add, defaults to ()
    :return: Extended tuple
    """
    if components is None:
        components = tuple()  # noqa: C408
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
    # components: tuple[type[PipelineComponent], ...] = (PipelineComponent,KubernetesApp,)
    components: tuple[type[PipelineComponent], ...] = ()
    if include_stock_components:
        components = _add_components("kpops.components")
    # Add custom components if provided
    if components_module:
        components = _add_components(components_module, components)
    if not components:
        msg = "No valid components found."
        raise RuntimeError(msg)

    # re-assign component type as Literal to work as discriminator
    for component in components:
        component.model_fields["type"] = FieldInfo(
            annotation=Literal[component.type],  # type: ignore[reportGeneralTypeIssues]
            default=component.type,
            # final=True,
            # title="Component type",
            # description=describe_object(component.__doc__),
            # model_config=BaseConfig,
            # class_validators=None,
        )
        extra_schema = {
            "type": "model-field",
            "schema": {
                "type": "literal",
                "expected": [component.type],
                "metadata": {
                    "pydantic.internal.needs_apply_discriminated_union": False
                },
            },
            "metadata": {
                "pydantic_js_functions": [],
                "pydantic_js_annotation_functions": [],
            },
        }
        if "schema" not in component.__pydantic_core_schema__["schema"]:
            component.__pydantic_core_schema__["schema"]["fields"][
                "type"
            ] = extra_schema
        else:
            component.__pydantic_core_schema__["schema"]["schema"]["fields"][
                "type"
            ] = extra_schema

    PipelineComponents = Union[components]  # type: ignore[valid-type]
    AnnotatedPipelineComponents = Annotated[
        PipelineComponents, Field(discriminator="type")
    ]

    class PipelineSchema(BaseModel):
        components: Sequence[AnnotatedPipelineComponents]

    schema = PipelineSchema.model_json_schema()

    # info, schema = models_json_schema(
    #     components_moded,
    #     title="KPOps pipeline schema",
    #     by_alias=True,
    #     # ref_template="#/definitions/{model}",
    # )
    print(json.dumps(schema, indent=4, sort_keys=True))

    # stripped_schema_first_item = {k[0]: v for k, v in schema[0].items()}
    # schema_first_item_adapted = {
    #     "discriminator": {
    #         "mapping": {},
    #         "propertyName": "type",
    #     },
    #     "oneOf": [],
    # }
    # mapping = {}
    # one_of = []
    # for k, v in stripped_schema_first_item.items():
    #     mapping[k.type] = v["$ref"]
    #     one_of.append(v)
    # schema_first_item_adapted["discriminator"]["mapping"] = mapping
    # schema_first_item_adapted["oneOf"] = one_of
    # complete_schema = schema[1].copy()
    # complete_schema["items"] = schema_first_item_adapted
    # complete_schema["type"] = "array"
    # print(
    #     json.dumps(
    #         complete_schema,
    #         indent=4,
    #         sort_keys=True,
    #     )
    # )

    # Create a type union that will hold the union of all component types
    # PipelineComponents = Union[components]  # type: ignore[valid-type]
    # AnnotatedPipelineComponents = Annotated[
    #     PipelineComponents, Field(discriminator="type")
    # ]
    # DumpablePipelineComponents = TypeAdapter(AnnotatedPipelineComponents)

    # schema = to_json(AnnotatedPipelineComponents)

    # print(schema)


def gen_config_schema() -> None:
    """Generate a json schema from the model of pipeline config."""
    schema = model_json_schema(KpopsConfig)
    print(json.dumps(schema, indent=4, sort_keys=True))
