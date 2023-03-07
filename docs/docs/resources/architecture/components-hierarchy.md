<!-- I dislike how the mermaid diagram looks, hence I drew it in draw.io. ~Ivan -->

<figure markdown>
  ![kpops-component-hierarchy](/images/kpops-components_class-diagram.png)
  <figcaption>KPOps component hierarchy</figcaption>
</figure>

<!-- ```mermaid
classDiagram
    BaseDefaultsComponent <|-- PipelineComponent
    PipelineComponent <|-- KafkaConnector
    PipelineComponent <|-- KubernetesApp
    KafkaConnector <|-- KafkaSourceConnector
    KafkaConnector <|-- KafkaSinkConnector
    KubernetesApp <|-- KafkaApp
    KafkaApp <|-- StreamsApp
    KafkaApp <|-- ProducerApp
    ``` -->
