# Overview 

This section explains the different components of KPOps, 
their usage and configuration in the pipeline 
definition [`pipeline.yaml`](../../../resources/pipeline-components/pipeline).

<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

```mermaid
flowchart BT
    PipelineComponent --> BaseDefaultsComponent
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
    click KafkaSourceConnector "../kafka-source-connector"
    click KafkaSinkConnector "../kafka-sink-connector"
```
<p style="text-align: center;"><i>KPOps component hierarchy</i></p>

<!-- Uncomment when page is created. -->
<!-- To learn more about KPOps' components hierarchy, visit the
[architecture](./docs/developer/architecture/component-inheritance.md) page. -->

