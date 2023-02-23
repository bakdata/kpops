# Components

This section explains the different components of KPOps, their usage and
configuration.
<!-- To learn more about their hierarchy, visit the
[architecture](/docs/developer/architecture/component-inheritance.md) page. -->

## KubernetesApp

### Usage

Can be used to deploy any app in Kubernetes using Helm, for example, a REST
service that serves Kafka data.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kubernetes-app.yaml
      --8<--
    ```

### Operations

#### deploy

Deploy using Helm.

#### destroy

Uninstall Helm release.

#### reset

Do nothing.

#### clean

Do nothing.

## KafkaApp

Sub class of [_KubernetesApp_](#kubernetesapp).

### Usage

- Defines a [streams-bootstrap](https://github.com/bakdata/streams-bootstrap#usage)
component
- Should not be used in `pipeline.yaml` as the component can be defined as either a
[StreamsApp](#streamsapp) or a [Producer](#producer)
- Often used in `defaults.yaml`

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kafka-app.yaml
      --8<--
    ```

### Operations

#### deploy

In addition to [KubernetesApp's](#kubernetesapp) `deploy`:

- Create topics if provided (optional)
- Submit Avro schemas to the registry if provided (optional)

#### destroy

Refer to [KubernetesApp](#kubernetesapp).

#### reset

Do nothing.

#### clean

Do nothing.

## StreamsApp

Sub class of [_KafkaApp_](#kafkaapp).

### Usage

Configures a
[streams-bootstrap](https://github.com/bakdata/streams-bootstrap)
[Kafka Streams app](https://github.com/bakdata/streams-bootstrap#kafka-streams)

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/streams-app.yaml
      --8<--
    ```

### Operations

#### deploy

Refer to [KafkaApp](#kafkaapp).

#### destroy

Refer to [KafkaApp](#kafkaapp).

#### [reset](https://github.com/bakdata/streams-bootstrap/tree/master/charts/streams-app-cleanup-job#streams-app-cleanup-helm-chart)

- Reset the consumer group offsets
- Reset Kafka Streams state

#### [clean](https://github.com/bakdata/streams-bootstrap/tree/master/charts/streams-app-cleanup-job#streams-app-cleanup-helm-chart)
<!-- same as reset, but `deleteOutput=true` -->

- Reset Kafka Streams state
- Delete the app's output topics
- Delete all associated schemas in the Schema Registry
- Delete the consumer group

## Producer

Sub class of [_KafkaApp_](#kafkaapp).

### Usage

Configures a
[streams-bootstrap](https://github.com/bakdata/streams-bootstrap)
[Kafka producer app](https://github.com/bakdata/streams-bootstrap#kafka-producer)

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/producer.yaml
      --8<--
    ```

### Operations

#### deploy

Refer to [KafkaApp](#kafkaapp).

#### destroy

Refer to [KafkaApp](#kafkaapp).

#### reset

Do nothing, producers are stateless.

#### [clean](https://github.com/bakdata/streams-bootstrap/tree/master/charts/producer-app-cleanup-job#producer-app-cleanup-helm-chart)

- Delete the output topics of the Kafka producer
- Delete all associated schemas in the Schema Registry

## KafkaSinkConnector

<!-- CHANGE LINK TO A DOCS PAGE WHEN CREATED -->
<!-- Sub class of [KafkaConnector](/docs/user/references/config.md) -->
Sub class of [KafkaConnector](https://github.com/bakdata/kpops/blob/main/kpops/components/base_components/kafka_connect.py#L35)

### Usage

Lets other systems pull data from Apache Kafka.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kafka-sink-connector.yaml
      --8<--
    ```

### Operations

#### deploy

- Add the sink connector to the Kafka Connect cluster
- Create the output topics if provided (optional)
- Register schemas in the Schema Registry if provided (optional)

#### destroy

The associated sink connector is removed.

#### [reset](https://github.com/bakdata/kafka-connect-resetter/#sink-resetter)

Reset the consumer group offsets.

#### clean

- Delete associated consumer group
- Delete configured error topics

## KafkaSourceConnector

<!-- CHANGE LINK TO A DOCS PAGE WHEN CREATED -->
<!-- Sub class of [KafkaConnector](/docs/user/references/config.md) -->
Sub class of [KafkaConnector](https://github.com/bakdata/kpops/blob/main/kpops/components/base_components/kafka_connect.py#L35)

### Usage

Manages source connectors in your Kafka Connect cluster.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kafka-source-connector.yaml
      --8<--
    ```

### Operations

#### deploy

- Add the source connector to the Kafka Connect cluster
- Create the output topics if provided (optional)
- Register schemas in the Schema registry if provided (optional)

#### destroy

Remove the source connector from the Kafka Connect cluster.

#### [reset](https://github.com/bakdata/kafka-connect-resetter/#source-resetter)

Delete state associated with the connector

#### clean

- Delete all associated output topics
- Delete all associated schemas in the Schema Registry
- Delete state associated with the connector
