from itertools import chain
from pathlib import Path
from typing import Annotated, Any, Optional, Sequence

from pydantic import Field, schema, schema_json_of
from pydantic.fields import ModelField
from pydantic.schema import SkipField

from kpops.cli.exception import ClassNotFoundError
from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import _find_classes
from kpops.components.base_components.kafka_connector import KafkaConnector

# from kpops.components.base_components.kubernetes_app import KubernetesApp
from kpops.components.base_components.pipeline_component import PipelineComponent


def write(contents: str, path: Path) -> None:
    with open(path, "w") as f:
        print(contents, file=f)


original_field_schema = schema.field_schema


# adapted from https://github.com/tiangolo/fastapi/issues/1378#issuecomment-764966955
def field_schema(field: ModelField, **kwargs: Any) -> Any:
    if field.field_info.extra.get("hidden_from_schema"):
        raise SkipField(f"{field.name} field is being hidden")
    else:
        return original_field_schema(field, **kwargs)


schema.field_schema = field_schema


def gen_pipeline_schema(
    components_module: Optional[str] = None,
    path: Path = Path(__file__).parents[2] / "docs/docs/schema/pipeline.json",
) -> None:

    components = _find_classes("kpops.components", PipelineComponent)
    if components_module:
        components = chain(
            components, _find_classes(components_module, PipelineComponent)
        )

    # Why doesnt KafkaConnector get found by _find_classes?
    PipelineComponent_ = KafkaConnector

    for component in components:
        try:
            PipelineComponent_ = PipelineComponent_ | component
        except (ClassNotFoundError):
            break

    AnnotatedPipelineComponent = Annotated[
        PipelineComponent_, Field(discriminator="schema_type")
    ]

    schema = schema_json_of(
        Sequence[AnnotatedPipelineComponent],
        title="kpops pipeline schema",
        by_alias=True,
        indent=4,
    ).replace("schema_type", "type")
    write(schema, path)


def gen_config_schema(
    path: Path = Path(__file__).parents[2] / "docs/docs/schema/config.json",
) -> None:
    schema = schema_json_of(PipelineConfig, title="kpops config schema", indent=4)
    write(schema, path)
