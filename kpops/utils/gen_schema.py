import inspect
import json
import logging
from abc import ABC
from collections.abc import Sequence
from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import (
    Field,
    RootModel,
    create_model,
)
from pydantic.fields import FieldInfo
from pydantic.json_schema import GenerateJsonSchema, model_json_schema
from pydantic_core.core_schema import (
    DefinitionsSchema,
    LiteralSchema,
    ModelField,
    ModelFieldsSchema,
)

from kpops.cli.registry import _find_classes
from kpops.components import (
    PipelineComponent,
)
from kpops.config import KpopsConfig


class SchemaScope(str, Enum):
    PIPELINE = "pipeline"
    DEFAULTS = "defaults"
    CONFIG = "config"


class MultiComponentGenerateJsonSchema(GenerateJsonSchema):
    ...


log = logging.getLogger("")


def _is_valid_component(
    defined_component_types: set[str],
    component: type[PipelineComponent],
    allow_abstract: bool,
) -> bool:
    """Check whether a PipelineComponent subclass has a valid definition for the schema generation.

    :param defined_component_types: types defined so far
    :param component: component type to be validated
    :return: Whether component is valid for schema generation
    """
    if not allow_abstract and (
        inspect.isabstract(component) or ABC in component.__bases__
    ):
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
    allow_abstract: bool = False,
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
        if _is_valid_component(defined_component_types, component, allow_abstract)
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
            annotation=Literal[component.type],  # type:ignore[valid-type]
            default=component.type,
            description="Component type",
        )
        core_schema: DefinitionsSchema = component.__pydantic_core_schema__  # pyright:ignore[reportGeneralTypeIssues]
        model_schema: ModelFieldsSchema = core_schema["schema"]["schema"]  # pyright:ignore[reportGeneralTypeIssues,reportTypedDictNotRequiredAccess]
        model_schema["fields"]["type"] = ModelField(
            type="model-field",
            schema=LiteralSchema(
                type="literal",
                expected=[component.type],
            ),
        )

    PipelineComponents = Union[components]  # type: ignore[valid-type]
    AnnotatedPipelineComponents = Annotated[
        PipelineComponents, Field(discriminator="type")
    ]

    class PipelineSchema(RootModel):
        root: Sequence[
            AnnotatedPipelineComponents  # pyright:ignore[reportGeneralTypeIssues]
        ]

    schema = PipelineSchema.model_json_schema(by_alias=True)
    print(json.dumps(schema, indent=4, sort_keys=True))


def gen_defaults_schema(
    components_module: str | None = None, include_stock_components: bool = True
) -> None:
    if not (include_stock_components or components_module):
        log.warning("No components are provided, no schema is generated.")
        return
    # Add stock components if enabled
    components: tuple[type[PipelineComponent], ...] = ()
    if include_stock_components:
        components = _add_components("kpops.components", allow_abstract=True)
    # Add custom components if provided
    if components_module:
        components = _add_components(components_module, components, allow_abstract=True)
    if not components:
        msg = "No valid components found."
        raise RuntimeError(msg)

    components_mapping: dict[str, Any] = {
        component.type: (component, ...) for component in components
    }
    DefaultsSchema = create_model("DefaultsSchema", **components_mapping)

    schema = DefaultsSchema.model_json_schema(by_alias=True)
    print(json.dumps(schema, indent=4, sort_keys=True))


def gen_config_schema() -> None:
    """Generate JSON schema from the model."""
    schema = model_json_schema(KpopsConfig)
    print(json.dumps(schema, indent=4, sort_keys=True))
