# Components

This section explains the different components of KPOps, their usage and
configuration. To learn more about their hierarchy, visit the
[architecture](/docs/developer/architecture/component-inheritance.md) page.

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

### deploy

Deploy using Helm.

### destroy

Uninstall Helm release.

### reset

Not implemented.

### clean

Not implemented.

## KafkaApp

Sub class of [_KubernetesApp_](#kubernetesapp).

### Usage

- Deploys a [streams-bootstrap](https://github.com/bakdata/streams-bootstrap)
component
- Not used in `pipeline.yaml` as the component can be defined as either a
[StreamsApp](#streamsapp) or a [Producer](#producer)
- Often used in `defaults.yaml`

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kafka-app.yaml
      --8<--
    ```

### deploy

In addition to [KubernetesApp's](#kubernetesapp) `deploy`:

- Create topics if provided (optional)
- Submit schemas to the registry if provided (optional)

### destroy

Refer to [KubernetesApp](#kubernetesapp).

### reset

Not implemented.

### clean

Not implemented.

## StreamsApp

Sub class of [_KafkaApp_](#kafkaapp).

### Usage

Configures a
[streams-bootstrap app](https://github.com/bakdata/streams-bootstrap) which in
turn configures a
[Kafka Streams app](https://kafka.apache.org/documentation/streams/).

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/streams-app.yaml
      --8<--
    ```

### deploy

Refer to [KafkaApp](#kafkaapp).

### destroy

Refer to [KafkaApp](#kafkaapp).

### reset

Runs a reset job in the cluster that is deleted by default after a succesful
completion.

- Reset the consumer group offsets
- Remove all streams' state

### clean

- Delete the app's output topics
- Delete all associated schemas in the Schema Registry
- Delete the consumer group

## Producer

Sub class of [_KafkaApp_](#kafkaapp).

### Usage

Publishes (writes) events to a Kafka cluster.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/producer.yaml
      --8<--
    ```


### deploy

Refer to [KafkaApp](#kafkaapp).

### destroy

Refer to [KafkaApp](#kafkaapp).

### reset

Not implemented, producers are stateless.

### clean

- Delete the output topics of the Kafka producer
- Delete all associated schemas in the Schema Registry

## KafkaSinkConnector

Sub class of [KafkaConnector](/docs/user/references/config.md)

### Usage

Lets other systems pull data from Apache Kafka.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kafka-sink-connector.yaml
      --8<--
    ```

### deploy

- Deploy the Kafka connector
- Create the output topics if provided (optional)
- Register schemas in the Schema registry if provided (optional)

### destroy

The associated Kafka connector is removed.

### reset

Reset the consumer group offsets.

### clean

- Delete associated consumer group
- Delete configured error topics

## KafkaSourceConnector

Sub class of [KafkaConnector](/docs/user/references/config.md)

### Usage

Lets other systems push data to Apache Kafka.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kafka-source-connector.yaml
      --8<--
    ```


### deploy

- Deploy the Kafka connector
- Create the output topics if provided (optional)
- Register schemas in the Schema registry if provided (optional)

### destroy

The associated Kafka connector is removed.

### reset

Remove all connect states.

### clean

- Delete all associated output topics
- Delete all associated schemas in the Schema Registry
