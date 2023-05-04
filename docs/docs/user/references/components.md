# Components

This section explains the different components of KPOps, their usage and configuration in the pipeline definition [`pipeline.yaml`](../../../resources/pipeline-components/pipeline).

--8<--
./docs/resources/architecture/components-hierarchy.md
--8<--

[See real-world examples of `pipeline.yaml`](../../../resources/examples/pipeline)

<!-- Uncomment when page is created. -->
<!-- To learn more about KPOps' components hierarchy, visit the
[architecture](/docs/developer/architecture/component-inheritance.md) page. -->

!!! note "Environment-specific pipeline definitions"
    Similarly to [defaults](../defaults/#configuration), it is possible to have an unlimited amount of additional environment-specific pipeline definitions. The naming convention is the same: add a suffix of the form `_{environment}` to the filename. Learn more about environments in the [Config](../config/#__codelineno-0-10) section.

## KubernetesApp

### Usage

Can be used to deploy any app in Kubernetes using Helm, for example, a REST service that serves Kafka data.

### Configuration

??? example "`pipeline.yaml`"

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

- Defines a [streams-bootstrap](https://github.com/bakdata/streams-bootstrap#usage){target=_blank} component
- Should not be used in `pipeline.yaml` as the component can be defined as either a [StreamsApp](#streamsapp) or a [Producer](#producer)
- Often used in `defaults.yaml`

### Configuration

??? example "`pipeline.yaml`"

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
[streams-bootstrap](https://github.com/bakdata/streams-bootstrap){target=_blank}
[Kafka Streams app](https://github.com/bakdata/streams-bootstrap#kafka-streams){target=_blank}

### Configuration

??? example "`pipeline.yaml`"

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

#### reset

- Reset the consumer group offsets
- Reset Kafka Streams state

#### clean
<!-- same as reset, but `deleteOutput=true` -->

- Reset Kafka Streams state
- Delete the app's output topics
- Delete all associated schemas in the Schema Registry
- Delete the consumer group

## Producer

Sub class of [_KafkaApp_](#kafkaapp).

### Usage

Configures a
[streams-bootstrap](https://github.com/bakdata/streams-bootstrap){target=_blank}
[Kafka producer app](https://github.com/bakdata/streams-bootstrap#kafka-producer){target=_blank}

### Configuration

??? example "`pipeline.yaml`"

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

#### clean

- Delete the output topics of the Kafka producer
- Delete all associated schemas in the Schema Registry

## KafkaSinkConnector

Sub class of [_KafkaConnector_](../defaults/#kafkaconnector).

### Usage

Lets other systems pull data from Apache Kafka.

### Configuration

??? example "`pipeline.yaml`"

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

#### reset

Reset the consumer group offsets using [bakdata's sink resetter](https://github.com/bakdata/kafka-connect-resetter/#sink-resetter){target=_blank}.

#### clean

- Delete associated consumer group
- Delete configured error topics

## KafkaSourceConnector

Sub class of [_KafkaConnector_](../defaults/#kafkaconnector).

### Usage

Manages source connectors in your Kafka Connect cluster.

### Configuration

??? example "`pipeline.yaml`"

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

#### reset

Delete state associated with the connector using [bakdata's sink resetter](https://github.com/bakdata/kafka-connect-resetter/#source-resetter){target=_blank}.

#### clean

- Delete all associated output topics
- Delete all associated schemas in the Schema Registry
- Delete state associated with the connector
