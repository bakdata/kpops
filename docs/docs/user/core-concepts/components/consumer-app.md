# ConsumerApp

Subclass of [_StreamsBootstrap_](streams-bootstrap.md).

### Usage

Configures a
[streams-bootstrap](https://github.com/bakdata/streams-bootstrap){target=_blank}
[Kafka consumer app](https://github.com/bakdata/streams-bootstrap#kafka-consumer){target=_blank}

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/consumer-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### Operations

#### deploy

Identical to [StreamsBootstrap's `deploy`](streams-bootstrap.md#deploy). The consumer app has no `to` section, so no topics are created and no schemas are submitted.

#### destroy

Uninstall Helm release.

#### reset

- Delete the consumer group offsets

#### clean

Similar to [`reset`](#reset) with an additional step:

- Delete persistent volume claims if `statefulSet` is enabled and `persistence` is enabled
