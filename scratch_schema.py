from typing import Annotated, Sequence

from pydantic import Field, schema_json_of

from kpops.components.streams_bootstrap.producer.producer_app import ProducerApp
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp

ComponentType = (
    StreamsApp
    | ProducerApp
    # | KafkaSourceConnector
    # | KafkaSinkConnector
    # | PipelineComponent
)


AnnotatedPipelineComponent = Annotated[
    ComponentType, Field(discriminator="discriminator")
]
schema = schema_json_of(
    Sequence[AnnotatedPipelineComponent],
    title="kpops pipeline schema",
    by_alias=True,
    indent=4,
)
print(schema)
