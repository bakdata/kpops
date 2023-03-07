# Defaults

KPOps has a very efficient way of dealing with repeating settings which manifests as [`defaults.yaml`](/resources/pipeline-defaults/defaults). This file provides the user with the power to set defaults for any and all [components](/user/references/components), thus omitting the need to repeat the same settings in [`pipeline.yaml`](/user/references/components).

??? "KPOps component Hierarchy"
    --8<--
    ./docs/resources/architecture/components-hierarchy.md
    --8<--

A very important mechanic of KPOps' defaults is that defaults set for a component apply to all components that inherit from it. An example can be found [here](#examples).

## Components

### [KubernetesApp](/user/references/components/#kubernetesapp)

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kubernetes-app.yaml
      --8<--
    ```

### KafkaApp

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-app.yaml
      --8<--
    ```

### StreamsApp

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-streams-app.yaml
      --8<--
    ```

### ProducerApp

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-producer.yaml
      --8<--
    ```

### KafkaConnector

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-connect.yaml
      --8<--
    ```

### KafkaSourceConnector

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-source-connector.yaml
      --8<--
    ```

### KafkaSinkConnector

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-sink-connector.yaml
      --8<--
    ```

## Examples

