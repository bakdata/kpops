```mermaid
classDiagram
    BaseDefaultsComponent <|-- PipelineComponent
    PipelineComponent <|-- KafkaConnector
    PipelineComponent <|-- KubernetesApp
    KafkaConnector <|-- KafkaSourceConnector
    KafkaConnector <|-- KafkaSinkConnector
    KubernetesApp <|-- KafkaApp
    KafkaApp <|-- StreamsApp
    KafkaApp <|-- ProducerApp
```
<p style="text-align: center;"><i>KPOps component hierarchy</i></p>
