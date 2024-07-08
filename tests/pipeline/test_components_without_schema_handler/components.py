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
                        _config=self._config,
                        _handlers=self._handlers,
                        name="sink-connector",
                        config=KafkaConnectorConfig(
                            **{
                                "topics": topic_name,
                                "transforms.changeTopic.replacement": f"{topic_name}-index-v1",
                            }
                        ),
                    )
                    inflate_steps.append(kafka_connector)

        return inflate_steps
