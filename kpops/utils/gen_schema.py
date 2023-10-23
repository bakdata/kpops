import inspect
import logging
from abc import ABC
from collections.abc import Sequence
from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseConfig, Field, schema, schema_json_of
from pydantic.fields import FieldInfo, ModelField
from pydantic.schema import SkipField

from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import _find_classes
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.docstring import describe_object


class SchemaScope(str, Enum):
    PIPELINE = "pipeline"
    CONFIG = "config"


original_field_schema = schema.field_schema


# adapted from https://github.com/tiangolo/fastapi/issues/1378#issuecomment-764966955
def field_schema(field: ModelField, **kwargs: Any) -> Any:
    if field.field_info.extra.get("hidden_from_schema"):
        msg = f"{field.name} field is being hidden"
        raise SkipField(msg)
    else:
        return original_field_schema(field, **kwargs)


schema.field_schema = field_schema

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
    components_module: str, components: tuple[type[PipelineComponent]] | None = None
) -> tuple[type[PipelineComponent]]:
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
    components: tuple[type[PipelineComponent]] = tuple()  # noqa: C408
    if include_stock_components:
        components = _add_components("kpops.components")
    # Add custom components if provided
    if components_module:
        components = _add_components(components_module, components)
    if not components:
        msg = "No valid components found."
        raise RuntimeError(msg)
    # Create a type union that will hold the union of all component types
    PipelineComponents = Union[components]  # type: ignore[valid-type]

    # re-assign component type as Literal to work as discriminator
    for component in components:
        component.__fields__["type"] = ModelField(
            name="type",
            type_=Literal[component.type],  # type: ignore[reportGeneralTypeIssues]
            required=False,
            default=component.type,
            final=True,
            field_info=FieldInfo(
                title="Component type",
                description=describe_object(component.__doc__),
            ),
            model_config=BaseConfig,
            class_validators=None,
        )

    AnnotatedPipelineComponents = Annotated[
        PipelineComponents, Field(discriminator="type")
    ]

    schema = schema_json_of(
        Sequence[AnnotatedPipelineComponents],
        title="KPOps pipeline schema",
        by_alias=True,
        indent=4,
        sort_keys=True,
    )
    print(schema)


def gen_config_schema() -> None:
    """Generate a json schema from the model of pipeline config."""
    schema = schema_json_of(
        PipelineConfig, title="KPOps config schema", indent=4, sort_keys=True
    )
    print(schema)
