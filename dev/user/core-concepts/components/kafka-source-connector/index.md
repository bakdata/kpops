# KafkaSourceConnector

Subclass of [*KafkaConnector*](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/kafka-connector/index.md>).

### Usage

Manages source connectors in your Kafka Connect cluster.

### Configuration

> [!NOTE]
>
> **`pipeline.yaml`**
>
> ```yaml
> # Kafka source connector
> - type: kafka-source-connector # required
>   name: kafka-source-connector # required
>   # Pipeline prefix that will prefix every component name. If you wish to not
>   # have any prefix you can specify an empty string.
>   prefix: ${pipeline.name}-
>   # Topic(s) into which the component will write output
>   to:
>     topics:
>       ${pipeline.name}-output-topic:
>         type: output # Implied when role is NOT specified
>       ${pipeline.name}-extra-topic:
>         label: topic-role # Implies `type` to be extra; Will throw an error if `type` is defined
>       ${pipeline.name}-error-topic:
>         type: error
>         # Currently KPOps supports Avro and JSON schemas.
>         key_schema: key-schema # must implement SchemaProvider to use
>         value_schema: value-schema
>         partitions_count: 1
>         replication_factor: 1
>         configs: # https://kafka.apache.org/documentation/#topicconfigs
>           cleanup.policy: compact
>     models: # SchemaProvider is initiated with the values given here
>       model: model
>   # Full documentation on connectors: https://kafka.apache.org/documentation/#connectconfigs
>   config: # required
>     tasks.max: 1
> ```

### Operations

#### deploy

- Add the source connector to the Kafka Connect cluster
- Create the output topics if provided (optional)
- Register schemas in the Schema registry if provided (optional)

#### destroy

Remove the source connector from the Kafka Connect cluster.

#### reset

Delete state associated with the connector using [bakdata's source resetter](<https://github.com/bakdata/kafka-connect-resetter/#source-resetter>).

#### clean

- Delete all associated output topics
- Delete all associated schemas in the Schema Registry
- Delete state associated with the connector
