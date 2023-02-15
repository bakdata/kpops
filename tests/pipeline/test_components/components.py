from typing import Any

from schema_registry.client.schema import AvroSchema
from typing_extensions import override

from kpops.component_handlers.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)
from kpops.components import KafkaSinkConnector
from kpops.components.base_components import PipelineComponent
from kpops.components.base_components.models.to_section import OutputTopicTypes
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp


class ImportProducer(ProducerApp):
    type: str = "scheduled-producer"


class Converter(StreamsApp):
    type: str = "converter"


class SubStreamsApp(StreamsApp):
    """Intermediary subclass of StreamsApp used for Filter."""


class Filter(SubStreamsApp):
    """Subsubclass of StreamsApp to test inheritance."""

    type: str = "filter"


class InflateStep(StreamsApp):
    type: str = "should-inflate"

    @override
    def inflate(self) -> list[PipelineComponent]:
        inflate_steps = super().inflate()
        if self.to:
            for topic_name, topic_config in self.to.topics.items():
                if topic_config.type == OutputTopicTypes.OUTPUT:
                    kafka_connector = KafkaSinkConnector(
                        name="sink-connector",
                        config=self.config,
                        handlers=self.handlers,
                        namespace="example-namespace",
                        app={  # type: ignore # FIXME
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
