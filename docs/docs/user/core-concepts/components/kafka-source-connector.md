# KafkaSourceConnector

Subclass of [_KafkaConnector_](./kafka-connector.md).

### Usage

Manages source connectors in your Kafka Connect cluster.

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/kafka-source-connector.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### Operations

#### deploy

- Add the source connector to the Kafka Connect cluster
- Create the output topics if provided (optional)
- Register schemas in the Schema registry if provided (optional)

#### destroy

Remove the source connector from the Kafka Connect cluster.

#### reset

Delete state associated with the connector using
[bakdata's source resetter](https://github.com/bakdata/kafka-connect-resetter/#source-resetter){target=_blank}.

#### clean

- Delete all associated output topics
- Delete all associated schemas in the Schema Registry
- Delete state associated with the connector
