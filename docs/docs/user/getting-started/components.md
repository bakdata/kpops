# Components

This section explains the different components of KPOps, their usage and configuration.

## KubernetesApp

### Usage

Can be used to deploy any app in Kubernetes using helm, for example, a REST Service that serves Kafka Data.

### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### Commands

#### deploy
#### destory
#### reset
#### clean

## KafkaApp

_KafkaApp_ inherits from [_KubernetesApp_](#kubernetesapp).

### Usage

Inherits from KubernetesApp. Often used in `defaults.yaml` Not usually used to deploy Kafka applications as they almost could be defined as either a _StreamsApp_ or a _Producer_.


### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### Commands

#### deploy
#### destory
#### reset
#### clean

## StreamsApp

_StreamsApp_ inherits from [_KafkaApp_](#kafkaapp).

### Usage

Configures a [streams bootstrap app](https://github.com/bakdata/streams-bootstrap) which in turns configures a [Kafka Streams app](https://kafka.apache.org/documentation/streams/)

### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### Commands

#### deploy

A Kubernetes deployment is created.
The output topics are created, and schemas are registered in the Schema registry if configured.

#### destory

The associated Kubernetes resources are removed.

#### reset

Kafka Streams apps are reset by resetting the consumer group offsets and removing all streams state.
This is achieved by running a reset job in the cluster that is deleted by default after it successfully runs.

#### clean

The output topics of the Kafka Streams app are deleted as well as all associated schemas in the Schema Registry.
Additionally, the consumer group is deleted.

## Producer

_Producer_ inherits from [_KafkaApp_](#kafkaapp).

### Usage

Publishes (write) events to a Kafka cluster.

### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### Commands

#### deploy

A Kubernetes job or cron job is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

#### destory

The associated Kubernetes resources are removed.

#### reset

Producers are not affected by reset as they are stateless.

#### clean

The output topics of the Kafka producer are deleted as well as all associated schemas in the Schema Registry.

## KafkaSinkConnector

### Usage

Lets other systems pull data from Apache Kafka.

### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### Commands

#### deploy

A Kafka connector is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

#### destory

The associated Kafka connector is removed.

#### reset

Kafka Sink Connectors are reset by resetting the consumer group offsets.

#### clean

Kafka Sink Connectors are cleaned by deleting their consumer group and deleting configured error topics.

## KafkaSourceConnector

### Usage

Lets other systems push data to Apache Kafka.

### Configuration

??? "Title (`file.yaml`)"
    Description

    ```yaml
    config:
    ```

### Commands

#### deploy

A Kafka connector is deployed.
The output topics are created, and schemas are registered in the Schema registry if configured.

#### destory

The associated Kafka connector is removed.

#### reset

Kafka Source Connectors are reset by removing all connect states.

#### clean

The output topics of the Kafka Source Connector are deleted as well as all associated schemas in the Schema Registry.

# Commands

This section will cover KPOps commands and how they differ depending on the component type.

These commands are
- deploy
- destroy
- reset
- clean

`KPOps` can apply the command only to a subset of steps by passing `--steps`.
The parameter takes a comma-separated string of the component's names.

You need to specify either `--dry-run` or `--execute` with each of these commands.

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
