# ConsumerProducerApp

Subclass of [_StreamsBootstrap_](streams-bootstrap.md).

### Usage

Configures a
[streams-bootstrap](https://github.com/bakdata/streams-bootstrap){target=_blank}
[Kafka ConsumerProducer app](https://github.com/bakdata/streams-bootstrap#kafka-consumerproducer){target=_blank}

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/consumer-producer-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### Operations

#### deploy

In addition to [StreamsBootstrap's `deploy`](streams-bootstrap.md#deploy):

- Create topics if provided (optional)
- Submit Avro schemas to the registry if provided (optional)

#### destroy

Uninstall Helm release.

#### reset

- Delete the consumer group offsets

#### clean

Similar to [`reset`](#reset) with additional steps:

- Delete the app's output topics
- Delete all associated schemas in the Schema Registry
- Delete persistent volume claims if `statefulSet` is enabled and `persistence` is enabled
