# Components

This section explains the different components of KPOps, their usage and configuration.
To learn more about their hierarchy, visit the
[architecture](/kpops/docs/docs/developer/architecture/component-inheritance.md)
page.

## KubernetesApp

### Usage

Can be used to deploy any app in Kubernetes using Helm, for example, a REST service that serves Kafka data.

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

Do nothing.

### clean

Do nothing.

## KafkaApp

Sub class of [_KubernetesApp_](#kubernetesapp).

### Usage

- Deploys a [streams-bootstrap](https://github.com/bakdata/streams-bootstrap) component.
- Not usually used in `pipeline.yaml` as the component can usually be defined as either a [StreamsApp](#streamsapp) or a [Producer](#producer).
- Often used in `defaults.yaml`.


### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kafka-app.yaml
      --8<--
    ```

### reset
### clean

## StreamsApp

_StreamsApp_ inherits from [_KafkaApp_](#kafkaapp).

### Usage

Configures a [streams bootstrap app](https://github.com/bakdata/streams-bootstrap) which in turns configures a [Kafka Streams app](https://kafka.apache.org/documentation/streams/)

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/streams-app.yaml
      --8<--
    ```


### deploy

A Kubernetes deployment is created.
The output topics are created, and schemas are registered in the Schema registry if configured.

### destory

The associated Kubernetes resources are removed.

### reset

Kafka Streams apps are reset by resetting the consumer group offsets and removing all streams state.
This is achieved by running a reset job in the cluster that is deleted by default after it successfully runs.

### clean

The output topics of the Kafka Streams app are deleted as well as all associated schemas in the Schema Registry.
Additionally, the consumer group is deleted.

## Producer

_Producer_ inherits from [_KafkaApp_](#kafkaapp).

### Usage

Publishes (write) events to a Kafka cluster.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/producer.yaml
      --8<--
    ```


### deploy

A Kubernetes job or cron job is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

### destory

The associated Kubernetes resources are removed.

### reset

Producers are not affected by reset as they are stateless.

### clean

The output topics of the Kafka producer are deleted as well as all associated schemas in the Schema Registry.

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

A Kafka connector is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

### destory

The associated Kafka connector is removed.

### reset

Kafka Sink Connectors are reset by resetting the consumer group offsets.

### clean

Kafka Sink Connectors are cleaned by deleting their consumer group and deleting configured error topics.

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

A Kafka connector is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

### destory

The associated Kafka connector is removed.

### reset

Kafka Source Connectors are reset by removing all connect states.

### clean

The output topics of the Kafka Source Connector are deleted as well as all associated schemas in the Schema Registry.

# Commands

<!--
## Deploy

The `kpops deploy` command creates the application resources.
We can update our deployment by changing its configuration and redeploying the pipeline.
If the data is incompatible with the currently deployed version, resetting or cleaning the pipeline might be necessary.

## Destroy

The `kpops destroy` command removes the application resources.

## Reset

The `kpops reset` command resets the state of applications and allows reprocessing of the data after a redeployment.

> The reset command does not affect output topics.
Running reset always includes running destroy.

Often, a reset job is deployed in the cluster that is deleted by default after running successfully.

## Clean

The `kpops clean` command removes all Kafka resources associated with a pipeline.

Running clean always includes running reset.

A clean job is often deployed in the cluster that is deleted by default after it successfully runs.
-->
