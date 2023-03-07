# Defaults

KPOps has a very efficient way of dealing with repeating settings which manifests as [`defaults.yaml`](/resources/pipeline-defaults/defaults). This file provides the user with the power to set defaults for any and all [components](/user/references/components), thus omitting the need to repeat the same settings in [`pipeline.yaml`](/resources/pipeline-components/pipeline).

A very important mechanic of KPOps' defaults is that defaults set for a component apply to all components that inherit from it. Examples can be found [here](/resources/examples/defaults).

??? "KPOps component Hierarchy"
    --8<--
    ./docs/resources/architecture/components-hierarchy.md
    --8<--

!!! tip inline end
    `defaults` is the default value of `defaults_filename_prefix`.
    It, together with `defaults_path` and  `environment` can be changed in [`config.yaml`](/user/references/config)

It is possible to set specific `defaults` for each `environment` by adding files called `defaults_{environment}.yaml` to the defaults folder at `defaults_path`. The defaults are loaded based on the currently set environment. It is important to note that `defaults_{environment}.yaml` overrides only the settings that are explicitly set to be different from the ones in the base `defaults` file.

## [KubernetesApp](/user/references/components/#kubernetesapp)

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kubernetes-app.yaml
      --8<--
    ```

## [KafkaApp](/user/references/components/#kafkaapp)

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-app.yaml
      --8<--
    ```

## [StreamsApp](/user/references/components/#streamsapp)

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-streams-app.yaml
      --8<--
    ```

## [ProducerApp](/user/references/components/#producerapp)

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-producer.yaml
      --8<--
    ```

## [KafkaConnector](#kafkaconnector)

`KafkaConnector` is a component that deploys [Kafka Connectors](https://kafka.apache.org/documentation.html#connect_configuring). Since a connector cannot be different from [sink](#kafkasinkconnector) or [source](#kafkasourceconnector), it is not recommended to use `KafkaConnector` for deployment in [`pipeline.yaml`](/resources/pipeline-components/pipeline).

Instead, `KafkaConnector` should be used in [`defaults.yaml`](/resources/pipeline-defaults/defaults) to set defaults for all connectors in the pipeline as they usually share a lot common settings.

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-connect.yaml
      --8<--
    ```

## [KafkaSourceConnector](/user/references/components/#kafkasourceconnector)

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-source-connector.yaml
      --8<--
    ```

## [KafkaSinkConnector](/user/references/components/#kafkasinkconnector)

??? "`defaults.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-defaults/defaults-kafka-sink-connector.yaml
      --8<--
    ```
