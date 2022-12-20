from typing import Any

from schema_registry.client.schema import AvroSchema
from typing_extensions import override

from kpops.components import KafkaSinkConnector
from kpops.components.base_components import PipelineComponent
from kpops.components.base_components.models.to_section import OutputTopicTypes
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp
from kpops.pipeline_deployer.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)


class ImportProducer(ProducerApp):
    _type = "scheduled-producer"


class Converter(StreamsApp):
    _type = "converter"


class SubStreamsApp(StreamsApp):
    """Intermediary subclass of StreamsApp used for Filter."""


class Filter(SubStreamsApp):
    """Subsubclass of StreamsApp to test inheritance."""

    _type = "filter"


class InflateStep(StreamsApp):
    _type = "should-inflate"

    @override
    def inflate(self) -> list[PipelineComponent]:
        inflate_steps: list[PipelineComponent] = [self]
        if self.to:
            for topic_name, topic_config in self.to.topics.items():
                if topic_config.type == OutputTopicTypes.OUTPUT:
                    kafka_connector = KafkaSinkConnector(
                        name="sink-connector",
                        config=self.config,
                        app={
                            "topics": topic_name,
                            "transforms.changeTopic.replacement": f"{topic_name}-index-v1",
                        },
                    )
                    inflate_steps.append(kafka_connector)

        return inflate_steps


class TestSchemaProvider(SchemaProvider):
    def provide_schema(self, schema_class: str, models: dict[str, Any]) -> Schema:
        schema = {
            "type": "record",
            "namespace": "KPOps",
            "name": "Employee",
            "fields": [
                {"name": "Name", "type": "string"},
                {"name": "Age", "type": "int"},
            ],
        }
        return AvroSchema(schema)
