# ProducerApp

Subclass of [_StreamsBootstrap_](streams-bootstrap.md).

### Usage

Configures a [streams-bootstrap](https://github.com/bakdata/streams-bootstrap){target=_blank} [Kafka producer app](https://github.com/bakdata/streams-bootstrap#kafka-producer){target=_blank}

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/producer-app.yaml
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

Do nothing, producers are stateless.

#### clean

- Delete the output topics of the Kafka producer
- Delete all associated schemas in the Schema Registry
