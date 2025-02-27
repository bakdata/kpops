# FIXME: pyright breaks here. Investigate why this is happening.
# type: ignore[reportGeneralTypeIssues]

import inspect
import json
import logging
from abc import ABC
from collections.abc import Sequence
from typing import Annotated, Any, Literal, Union

from pydantic import (
    BaseModel,
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

from kpops.components.base_components.pipeline_component import (
    PipelineComponent,
)
from kpops.config import KpopsConfig
from kpops.core.registry import Registry


class MultiComponentGenerateJsonSchema(GenerateJsonSchema): ...


log = logging.getLogger("")

registry = Registry()
registry.discover_components()
COMPONENTS = tuple(registry.components)


def print_schema(model: type[BaseModel]) -> None:
    schema = model_json_schema(model, by_alias=True)
    print(json.dumps(schema, indent=4, sort_keys=True))


def _is_valid_component(
    component: type[PipelineComponent],
    allow_abstract: bool,
) -> bool:
    """Check whether a PipelineComponent subclass has a valid definition for the schema generation.

    :param component: component type to be validated
    :param allow_abstract: whether to include abstract components marked as ABC
    :return: Whether component is valid for schema generation
    """
    if not allow_abstract and (
        inspect.isabstract(component) or ABC in component.__bases__
    ):
        log.warning(f"SKIPPED {component.__name__}, component is abstract.")
        return False
    return True


def gen_pipeline_schema() -> None:
    """Generate a JSON schema from the models of pipeline components."""
    components = [
        component for component in COMPONENTS if _is_valid_component(component, False)
    ]
    # re-assign component type as Literal to work as discriminator
    for component in components:
        component.model_fields["type"] = FieldInfo(
            annotation=Literal[component.type],  # pyright: ignore[reportArgumentType]
            default=component.type,
        )
        core_schema: DefinitionsSchema = component.__pydantic_core_schema__  # pyright: ignore[reportAssignmentType]
        schema = core_schema
        while "schema" in schema:
            schema = schema["schema"]
        model_schema: ModelFieldsSchema = schema  # pyright: ignore[reportAssignmentType]
        model_schema["fields"]["type"] = ModelField(
            type="model-field",
            schema=LiteralSchema(
                type="literal",
                expected=[component.type],
            ),
        )

    PipelineComponents = Union[tuple(components)]  # pyright: ignore[reportInvalidTypeArguments,reportGeneralTypeIssues]
    AnnotatedPipelineComponents = Annotated[
        PipelineComponents, Field(discriminator="type")
    ]

    class PipelineSchema(RootModel[Sequence[AnnotatedPipelineComponents]]):
        root: Sequence[
            AnnotatedPipelineComponents  # pyright: ignore[reportInvalidTypeForm]
        ]

    print_schema(PipelineSchema)


def gen_defaults_schema() -> None:
    components = [
        component for component in COMPONENTS if _is_valid_component(component, True)
    ]
    components_mapping: dict[str, Any] = {
        component.type: (component, ...) for component in components
    }
    DefaultsSchema = create_model("DefaultsSchema", **components_mapping)
    print_schema(DefaultsSchema)


def gen_config_schema() -> None:
    """Generate JSON schema from the model."""
    print_schema(KpopsConfig)
