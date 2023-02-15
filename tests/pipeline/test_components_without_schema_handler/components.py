from typing_extensions import override

from kpops.component_handlers.kafka_connect.model import KafkaConnectConfig
from kpops.components import KafkaSinkConnector
from kpops.components.base_components import PipelineComponent
from kpops.components.base_components.models.to_section import OutputTopicTypes
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp


class ImportProducer(ProducerApp):
    type: str = "scheduled-producer"


class Converter(StreamsApp):
    type: str = "converter"


class InflateStep(StreamsApp):
    type: str = "should-inflate"

    @override
    def inflate(self) -> list[PipelineComponent]:
        inflate_steps: list[PipelineComponent] = [self]
        if self.to:
            for topic_name, topic_config in self.to.topics.items():
                if topic_config.type == OutputTopicTypes.OUTPUT:
                    kafka_connector = KafkaSinkConnector(
                        name="sink-connector",
                        config=self.config,
                        handlers=self.handlers,
                        namespace="example-namespace",
                        app=KafkaConnectConfig(
                            **{
                                "topics": topic_name,
                                "transforms.changeTopic.replacement": f"{topic_name}-index-v1",
                            }
                        ),
                    )
                    inflate_steps.append(kafka_connector)

        return inflate_steps
