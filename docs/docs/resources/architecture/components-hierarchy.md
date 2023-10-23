```mermaid
flowchart BT
    KubernetesApp --> PipelineComponent
    KafkaConnector --> PipelineComponent
    KafkaApp --> KubernetesApp
    StreamsApp --> KafkaApp
    ProducerApp --> KafkaApp
    KafkaSourceConnector --> KafkaConnector
    KafkaSinkConnector --> KafkaConnector
    
    click KubernetesApp "../kubernetes-app"
    click KafkaApp "../kafka-app"
    click StreamsApp "../streams-app"
    click ProducerApp "../producer-app"
    click KafkaConnector "../kafka-connector"
    click KafkaSourceConnector "../kafka-source-connector"
    click KafkaSinkConnector "../kafka-sink-connector"
```

<p style="text-align: center;"><i>KPOps component hierarchy</i></p>
