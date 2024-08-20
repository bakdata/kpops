# StreamsApp

Subclass of and [_StreamsBootstrap_](streams-bootstrap.md).

### Usage

Configures a
[streams-bootstrap](https://github.com/bakdata/streams-bootstrap){target=_blank}
[Kafka Streams app](https://github.com/bakdata/streams-bootstrap#kafka-streams){target=_blank}

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/streams-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### Operations

#### deploy

In addition to [KubernetesApp's `deploy`](kubernetes-app.md#deploy):

- Create topics if provided (optional)
- Submit Avro schemas to the registry if provided (optional)

#### destroy

Uninstall Helm release.

#### reset

- Delete the consumer group offsets
- Delete Kafka Streams state

#### clean

Similar to [`reset`](#reset) with to additional steps:

- Delete the app's output topics
- Delete all associated schemas in the Schema Registry
