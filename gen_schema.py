import json
from pathlib import Path
from typing import Annotated, Any, Mapping, Sequence

from apischema.discriminators import Discriminator
from apischema.json_schema import deserialization_schema

from kpops.cli.pipeline_config import PipelineConfig
from kpops.components.base_components.kafka_app import KafkaApp
from kpops.components.base_components.kafka_connect import (
    KafkaSinkConnector,
    KafkaSourceConnector,
)
from kpops.components.base_components.kubernetes_app import KubernetesApp
from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp


def write(schema: Mapping[str, Any], path: Path) -> None:
    with open(path, "w") as f:
        print(json.dumps(schema, indent=4), file=f)


PipelineComponent = (
    KubernetesApp
    | KafkaApp
    | StreamsApp
    | ProducerApp
    | KafkaSourceConnector
    | KafkaSinkConnector
)


def gen_discriminator_mapping(
    _alias: str, classes: Sequence[PipelineComponent]
) -> dict[str, PipelineComponent]:
    return {_class.type: _class for _class in classes}


Pipeline = Annotated[
    PipelineComponent,
    Discriminator(
        "type",
        gen_discriminator_mapping,
    ),
]


schema = deserialization_schema(Pipeline)
write(schema, Path("schema_pipeline.json"))

schema = deserialization_schema(PipelineConfig)
write(schema, Path("schema_config.json"))
