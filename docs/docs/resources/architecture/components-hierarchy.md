```mermaid
flowchart BT
    KubernetesApp --> PipelineComponent
    HelmApp --> KubernetesApp
    KafkaApp --> HelmApp
    StreamsApp --> KafkaApp
    ProducerApp --> KafkaApp
    KafkaConnector --> PipelineComponent
    KafkaSourceConnector --> KafkaConnector
    KafkaSinkConnector --> KafkaConnector

    click KubernetesApp "/kpops/user/core-concepts/components/kubernetes-app"
    click HelmApp "/kpops/user/core-concepts/components/helm-app"
    click KafkaApp "/kpops/user/core-concepts/components/kafka-app"
    click StreamsApp "/kpops/user/core-concepts/components/streams-app"
    click ProducerApp "/kpops/user/core-concepts/components/producer-app"
    click KafkaConnector "/kpops/user/core-concepts/components/kafka-connector"
    click KafkaSourceConnector "/kpops/user/core-concepts/components/kafka-source-connector"
    click KafkaSinkConnector "/kpops/user/core-concepts/components/kafka-sink-connector"
```

<p style="text-align: center;"><i>KPOps component hierarchy</i></p>
