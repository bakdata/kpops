from schema_registry.client.schema import AvroSchema
from typing_extensions import override

from kpops.component_handlers.schema_handler.schema_provider import (
    Schema,
    SchemaProvider,
)
from kpops.components import (
    KafkaSinkConnector,
    PipelineComponent,
    ProducerApp,
    StreamsApp,
)
from kpops.components.base_components.models import ModelName, ModelVersion, TopicName
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)


class ScheduledProducer(ProducerApp):
    ...


class Converter(StreamsApp):
    ...


class SubStreamsApp(StreamsApp):
    """Intermediary subclass of StreamsApp used for Filter."""


class Filter(SubStreamsApp):
    """Subsubclass of StreamsApp to test inheritance."""


class ShouldInflate(StreamsApp):
    @override
    def inflate(self) -> list[PipelineComponent]:
        inflate_steps = super().inflate()
        if self.to:
            for topic_name, topic_config in self.to.topics.items():
                if topic_config.type == OutputTopicTypes.OUTPUT:
                    kafka_connector = KafkaSinkConnector(
                        name=f"{self.name}-inflated-sink-connector",
                        config=self.config,
                        handlers=self.handlers,
                        app={  # type: ignore[reportGeneralTypeIssues], required `connector.class` comes from defaults during enrichment
                            "topics": topic_name,
                            "transforms.changeTopic.replacement": f"{topic_name}-index-v1",
                        },
                        to=ToSection(
                            topics={
                                TopicName("${component.type}"): TopicConfig(
                                    type=OutputTopicTypes.OUTPUT
                                ),
                                TopicName("${component.name}"): TopicConfig(
                                    type=None, role="test"
                                ),
                            }
                        ),
                    )
                    inflate_steps.append(kafka_connector)
                    streams_app = StreamsApp(
                        name=f"{self.name}-inflated-streams-app",
                        config=self.config,
                        handlers=self.handlers,
                        to=ToSection(  # type: ignore[reportGeneralTypeIssues]
                            topics={
                                TopicName(
                                    f"{self.full_name}-" + "${component.name}"
                                ): TopicConfig(type=OutputTopicTypes.OUTPUT)
                            }
                        ).model_dump(),
                    )
                    inflate_steps.append(streams_app)

        return inflate_steps


class TestSchemaProvider(SchemaProvider):
    def provide_schema(
        self, schema_class: str, models: dict[ModelName, ModelVersion]
    ) -> Schema:
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


class InflateBadly(StreamsApp):
    def inflate(self) -> list[PipelineComponent]:
        connector = KafkaSinkConnector(
            name="inflated-connector-name",
            config=self.config,
            handlers=self.handlers,
            app={},  # type: ignore[reportArgumentType]
        )
        return [self, connector]
