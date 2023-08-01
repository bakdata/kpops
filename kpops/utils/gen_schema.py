import logging
from enum import Enum
from typing import Annotated, Any, Literal, Sequence, Union

from pydantic import Field, schema, schema_json_of
from pydantic.fields import FieldInfo, ModelField
from pydantic.schema import SkipField

from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import _find_classes
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.utils.docstring import describe_attr, describe_object


class SchemaScope(str, Enum):
    PIPELINE = "pipeline"
    CONFIG = "config"


original_field_schema = schema.field_schema


# adapted from https://github.com/tiangolo/fastapi/issues/1378#issuecomment-764966955
def field_schema(field: ModelField, **kwargs: Any) -> Any:
    if field.field_info.extra.get("hidden_from_schema"):
        raise SkipField(f"{field.name} field is being hidden")
    else:
        return original_field_schema(field, **kwargs)


schema.field_schema = field_schema

log = logging.getLogger("")


def _is_valid_component(
    defined_component_types: set[str], component: type[PipelineComponent]
) -> bool:
    """
    Check whether a PipelineComponent subclass has a valid definition for the schema generation.

    :param defined_component_types: types defined so far
    :type defined_component_types: list[str]
    :param component: component type to be validated
    :type component: type[PipelineComponent]
    :return: Whether component is valid for schema generation
    :rtype: bool
    """
    component_type = component.get_component_type()
    if component_type in defined_component_types:
        log.warning(f"SKIPPED {component.__name__}, component type must be unique.")
        return False
    else:
        defined_component_types.add(component_type)
        return True


def _add_components(
    components_module: str, components: tuple[type[PipelineComponent]] | None = None
) -> tuple[type[PipelineComponent]]:
    """Add components to a components tuple

    If an empty tuple is provided or it is not provided at all, the components
    types from the given module are 'tupled'

    :param components_module: Python module. Only the classes that inherit from
        PipelineComponent will be considered.
    :type components_module: str
    :param components: Tuple of components to which to add, defaults to ()
    :type components: tuple, optional
    :return: Extended tuple
    :rtype: tuple
    """
    if components is None:
        components = tuple()
    # Set of existing types, against which to check the new ones
    defined_component_types: set[str] = {
        component.get_component_type() for component in components
    }
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
    :type components_module: str or None, optional
    :param include_stock_components: Whether to include the stock components,
        defaults to True
    :type include_stock_components: bool, optional
    :rtype: None
    """
    if not (include_stock_components or components_module):
        log.warning("No components are provided, no schema is generated.")
        return
    # Add stock components if enabled
    components: tuple[type[PipelineComponent]] = tuple()
    if include_stock_components:
        components = tuple(_find_classes("kpops.components", PipelineComponent))
    # Add custom components if provided
    if components_module:
        components = _add_components(components_module, components)
    # Create a type union that will hold the union of all component types
    PipelineComponents = Union[components]  # type: ignore[valid-type]

    # re-assign component type as Literal to work as discriminator
    for component in components:
        component_type = component.get_component_type()
        component.__fields__["type"] = ModelField(
            name="type",
            type_=Literal[component_type],  # type: ignore
            required=False,
            default=component_type,
            final=True,
            field_info=FieldInfo(
                title=describe_attr("type", component.__doc__),
                description=describe_object(component.__doc__),
            ),
            model_config=component.Config,
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
    """Generate a json schema from the model of pipeline config"""
    schema = schema_json_of(
        PipelineConfig, title="KPOps config schema", indent=4, sort_keys=True
    )
    print(schema)
