# KafkaConnector

`KafkaConnector` is a component that deploys [Kafka Connectors](https://kafka.apache.org/documentation.html#connect_configuring){target=_blank}. Since a connector cannot be different from sink or source it is not recommended to use `KafkaConnector` for deployment in [`pipeline.yaml`](../../../resources/pipeline-components/pipeline.md). Instead, `KafkaConnector` should be used in [`defaults.yaml`](../defaults.md#kafkaconnector) to set defaults for all connectors in the pipeline as they can share some common settings.
