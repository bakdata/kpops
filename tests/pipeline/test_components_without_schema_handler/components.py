from typing_extensions import override

from kpops.component_handlers.kafka_connect.model import KafkaConnectorConfig
from kpops.components import (
    KafkaSinkConnector,
    PipelineComponent,
    ProducerApp,
    StreamsApp,
)
from kpops.components.base_components.models.topic import OutputTopicTypes


class ScheduledProducer(ProducerApp): ...


class Converter(StreamsApp): ...


class ShouldInflate(StreamsApp):
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
                        app=KafkaConnectorConfig(
                            **{
                                "topics": topic_name,
                                "transforms.changeTopic.replacement": f"{topic_name}-index-v1",
                            }
                        ),
                    )
                    inflate_steps.append(kafka_connector)

        return inflate_steps
