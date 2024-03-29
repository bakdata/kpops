# KafkaApp

Subclass of [_HelmApp_](helm-app.md).

### Usage

- Defines a [streams-bootstrap](https://github.com/bakdata/streams-bootstrap#usage){target=_blank} component
- Should not be used in `pipeline.yaml` as the component can be defined as either a [StreamsApp](streams-app.md) or a [ProducerApp](producer-app.md)
- Often used in `defaults.yaml`

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/kafka-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### Operations

#### deploy

In addition to [HelmApp's `deploy`](helm-app.md#deploy):

- Create topics if provided (optional)
- Submit Avro schemas to the registry if provided (optional)

#### destroy

Uninstall Helm release.

#### reset

Do nothing.

#### clean

Do nothing.
