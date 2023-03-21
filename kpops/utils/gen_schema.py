from pathlib import Path
from typing import Annotated, Any, Sequence, Optional, Union

from pydantic import Field, schema, schema_json_of
from pydantic.fields import ModelField
from pydantic.schema import SkipField

from kpops.cli.pipeline_config import PipelineConfig
from kpops.cli.registry import Registry, ClassDict, find_class, _find_classes
from kpops.components.base_components.pipeline_component import PipelineComponent
from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.base_components.kafka_connector import (
    KafkaConnector,
    KafkaSinkConnector,
    KafkaSourceConnector,
)
from kpops.components.base_components.kubernetes_app import KubernetesApp
from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp
from kpops.pipeline_generator.pipeline import Pipeline
from kpops.cli.exception import ClassNotFoundError

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

def gen_pipeline_schema(components_module: Optional[str] = None, path: Path = Path(__file__).parents[2] / "docs/docs/schema/pipeline.json") -> None:

    # Why doesnt KafkaConnector get found by _find_classes?
    PipelineComponent_ = KafkaConnector

    for component in _find_classes("kpops.components", PipelineComponent):
        try:
            PipelineComponent_ = PipelineComponent_ | component
        except(ClassNotFoundError):
            break

    if components_module:
        for component in _find_classes("kpops.components", PipelineComponent):
            try:
                PipelineComponent_ = PipelineComponent_ | component
            except(ClassNotFoundError):
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

def gen_config_schema(path: Path = Path(__file__).parents[2] / "docs/docs/schema"):
    schema = schema_json_of(PipelineConfig, title="kpops config schema", indent=4)
    write(schema, path / "config.json")
