# Overview

This section explains the different components of KPOps, their usage and configuration in the pipeline definition [`pipeline.yaml`](<https://bakdata.github.io/kpops/dev/resources/pipeline-components/pipeline/index.md>).

```
flowchart BT
    KubernetesApp --> PipelineComponent
    HelmApp --> KubernetesApp
    KafkaApp --> PipelineComponent
    StreamsBootstrap --> KafkaApp
    StreamsBootstrap --> HelmApp
    StreamsApp --> StreamsBootstrap
    ProducerApp --> StreamsBootstrap
    ConsumerApp --> StreamsBootstrap
    ConsumerProducerApp --> StreamsBootstrap
    KafkaConnector --> KafkaApp
    KafkaSourceConnector --> KafkaConnector
    KafkaSinkConnector --> KafkaConnector

    click KubernetesApp "./../kubernetes-app"
    click HelmApp "./../helm-app"
    click StreamsBootstrap "./../streams-bootstrap"
    click StreamsApp "./../streams-app"
    click ProducerApp "./../producer-app"
    click ConsumerApp "./../consumer-app"
    click ConsumerProducerApp "./../consumer-producer-app"
    click KafkaConnector "./../kafka-connector"
    click KafkaSourceConnector "./../kafka-source-connector"
    click KafkaSinkConnector "./../kafka-sink-connector"
```

*KPOps component hierarchy*
