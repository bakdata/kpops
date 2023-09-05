# KafkaSinkConnector

Subclass of [_KafkaConnector_](./kafka-connector.md).

### Usage

Lets other systems pull data from Apache Kafka.

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/kafka-sink-connector.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### Operations

#### deploy

- Add the sink connector to the Kafka Connect cluster
- Create the output topics if provided (optional)
- Register schemas in the Schema Registry if provided (optional)

#### destroy

The associated sink connector is removed from the Kafka Connect cluster.

#### reset

Reset the consumer group offsets using
[bakdata's sink resetter](https://github.com/bakdata/kafka-connect-resetter/#sink-resetter){target=_blank}.

#### clean

- Delete associated consumer group
- Delete configured error topics
