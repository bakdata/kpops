# Working with KPOps

## Components

This section explains the different components of KPOps, their usage and configuration.

### KubernetesApp

#### Usage

Can be used to deploy any app in Kubernetes using helm. An example is a Redis database.

#### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### StreamsApp

#### Usage

Configures a [streams bootstrap app](https://github.com/bakdata/streams-bootstrap) which in turns configures a [Kafka Streams app](https://kafka.apache.org/documentation/streams/)

#### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### Producer

#### Usage

Publish (write) events to a Kafka cluster.

#### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### KafkaSinkConnector

#### Usage

Let other systems pull data from Apache Kafka.

#### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### KafkaSourceConnector

#### Usage

Let other systems push data to Apache Kafka.

#### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

## Commands

This section will cover KPOps commands and how they differ depending on the component type.

These commands are
- deploy
- destroy
- reset
- clean

`KPOps` can apply the command only to a subset of steps by passing `--steps`.
The parameter takes a comma-separated string of the component's names.

You need to specify either `--dry-run` or `--execute` with each of these commands.

### Deploy

The `kpops deploy` command creates the application resources.
We can update our deployment by changing its configuration and redeploying the pipeline.
If the data is incompatible with the currently deployed version, resetting or cleaning the pipeline might be necessary.

#### Kafka Producer

A Kubernetes job or cron job is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

#### Kafka Streams

A Kubernetes deployment is created.
The output topics are created, and schemas are registered in the Schema registry if configured.

#### Kafka Connect

A Kafka connector is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

### Destroy

The `kpops destroy` command removes the application resources.

#### Kafka Producer

The associated Kubernetes resources are removed.

#### Kafka Streams

The associated Kubernetes resources are removed.

#### Kafka Connect

The associated Kafka connector is removed.

### Reset

The `kpops reset` command resets the state of applications and allows reprocessing of the data after a redeployment.

> The reset command does not affect output topics.
Running reset always includes running destroy.

Often, a reset job is deployed in the cluster that is deleted by default after running successfully.

#### Kafka Producer

Producers are not affected by reset as they are stateless.

#### Kafka Streams

Kafka Streams apps are reset by resetting the consumer group offsets and removing all streams state.
This is achieved by running a reset job in the cluster that is deleted by default after it successfully runs.

#### Kafka Connect

##### Sinks Connectors

Kafka Sink Connectors are reset by resetting the consumer group offsets.

##### Source Connectors

Kafka Source Connectors are reset by removing all connect states.

### Clean

The `kpops clean` command removes all Kafka resources associated with a pipeline.

Running clean always includes running reset.

A clean job is often deployed in the cluster that is deleted by default after it successfully runs.

#### Kafka Producer

The output topics of the Kafka producer are deleted as well as all associated schemas in the Schema Registry.

#### Kafka Streams

The output topics of the Kafka Streams app are deleted as well as all associated schemas in the Schema Registry.
Additionally, the consumer group is deleted.

#### Kafka Connect

##### Sinks Connectors

Kafka Sink Connectors are cleaned by deleting their consumer group and deleting configured error topics.

##### Source Connectors

The output topics of the Kafka Source Connector are deleted as well as all associated schemas in the Schema Registry.
