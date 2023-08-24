# Defaults

KPOps has a very efficient way of dealing with repeating settings which manifests as [`defaults.yaml`](../../../resources/pipeline-defaults/defaults). This file provides the user with the power to set defaults for any and all [components](./components/overview.md), thus omitting the need to repeat the same settings in [`pipeline.yaml`](../../../resources/pipeline-components/pipeline).

[See real-world examples for `defaults`](../../../resources/examples/defaults).

## Features

### Inheritance

An important mechanic of KPOps is that `defaults` set for a component apply to all components that inherit from it.

It is possible, although not recommended, to add settings that are specific to a component's subclass. An example would be configuring `offset_topic` under `kafka-connector` instead of `kafka-source-connector`.

### Configuration

It is possible to set specific `defaults` for each `environment` by adding files called `defaults_{environment}.yaml` to the defaults folder at `defaults_path`. The defaults are loaded based on the currently set environment.

It is important to note that `defaults_{environment}.yaml` overrides only the settings that are explicitly set to be different from the ones in the base `defaults` file.

<!-- dprint-ignore-start -->

!!! tip
    `defaults` is the default value of `defaults_filename_prefix`.
    Together with `defaults_path` and `environment` it can be changed in [`config.yaml`](../config/#__codelineno-0-16)

<!-- dprint-ignore-end -->

## Components

<!-- When possible, automatically generate a list of all component-specific settings under each component. -->

The `defaults` codeblocks in this section contain the full set of settings that are specific to the component. If a setting already exists in a parent config, it will not be included in the child's.

### [KubernetesApp](./components/kubernetes-app.md)

<!-- dprint-ignore-start -->

??? example "`defaults.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-defaults/defaults-kubernetes-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### [KafkaApp](./components/kafka-app.md)

<!-- dprint-ignore-start -->

??? example "`defaults.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-defaults/defaults-kafka-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### [StreamsApp](./components/streams-app.md)

<!-- dprint-ignore-start -->

??? example "`defaults.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-defaults/defaults-streams-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### [ProducerApp](./components/producer-app.md)

<!-- dprint-ignore-start -->

??? example "`defaults.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-defaults/defaults-producer.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### [KafkaConnector](./components/kafka-connector.md)

<!-- dprint-ignore-start -->

??? example "`defaults.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-defaults/defaults-kafka-connector.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### [KafkaSourceConnector](./components/kafka-source-connector.md)

<!-- dprint-ignore-start -->

??? example "`defaults.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-defaults/defaults-kafka-source-connector.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### [KafkaSinkConnector](./components/kafka-sink-connector.md)

<!-- dprint-ignore-start -->

??? example "`defaults.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-defaults/defaults-kafka-sink-connector.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->
