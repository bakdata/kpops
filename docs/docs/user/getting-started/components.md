# Components

This section explains the different components of KPOps, their usage and configuration.
To learn more about their hierarchy, visit the
[architecture](/kpops/docs/docs/developer/architecture/component-inheritance.md)
page.

## KubernetesApp

### Usage

Can be used to deploy any app in Kubernetes using helm, for example, a REST Service that serves Kafka Data.

### Configuration

??? "`pipeline.yaml`"

    ```yaml
      # Base Kubernetes App
    - type: kubernetes-app
      name: kubernetes-app # required
      namespace: namespace # required
      # `app` contains application-specific settings, hence it does not have a rigid
      # structure. The fields below are just an example.
      app: # required
        key1:
          key4: value3
        key2: value1
        key3: value2
      # Topic(s) from which the component will read input
      from:
        topics: # required
          ${pipeline_name}-input-topic:
            type: input # required
            role: topic-role
      # Topic(s) into which the component will write output
      to:
        topics: # required
          ${pipeline_name}-output-topic:
            type: output # required
            role: topic-role
            keySchema: key-schema
            valueSchema: value-schema
            partitions_count: 1
            replication_factor: 1
            configs: 
              config1: config1
        models: 
          model: model
      # Pipeline prefix that will prefix every component name. If you wish to not 
      # have any prefix you can specify an empty string.
      prefix: ${pipeline_name}-
      # Helm repository configuration
      repoConfig:
        repositoryName: my-repo # required
        url: https://bakdata.github.io/ # required
        repoAuthFlags: 
          username: user
          password: pass
          ca_file: /home/user/path/to/ca-file
          insecure_skip_tls_verify: false
      version: 1.0.0
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

??? "`pipeline.yaml`"

    ```yaml
      # Base component for Kafka-based components.
      # Producer or streaming apps should inherit from this class.
      - type: kafka-app # required
        name: kafka-app # required
        namespace: namespace # required
        # `app` can contain application-specific settings, hence  the user is free to
        # add the key-value pairs they need. The fields that are specific to kafka
        # apps are marked with `# kafka-app-specific`
        app: # required
          streams: # required, kafka-app-specific
            brokers: ${broker} # required
            schemaRegistryUrl: ${schema_registry_url}
          nameOverride: override-with-this-name # kafka-app-specific
          key1:
            key4: value3
          key2: value1
          key3: value2
        # Topic(s) from which the component will read input
        from:
          topics: # required
            ${pipeline_name}-input-topic:
              type: input # required
              role: topic-role
        # Topic(s) into which the component will write output
        to:
          topics: # required
            ${pipeline_name}-output-topic:
              type: output # required
              role: topic-role
              keySchema: key-schema
              valueSchema: value-schema
              partitions_count: 1
              replication_factor: 1
              configs: 
                config1: config1
          models: 
            model: model
        # Pipeline prefix that will prefix every component name. If you wish to not 
        # have any prefix you can specify an empty string.
        prefix: ${pipeline_name}-
        # Helm repository configuration, the default value is given here
        repoConfig:
          repositoryName: bakdata-streams-bootstrap # required
          url: https://bakdata.github.io/streams-bootstrap/ # required
          repo_auth_flags:
            username: user
            password: pass
            ca_file: /home/user/path/to/ca-file
            insecure_skip_tls_verify: false
        version: "2.7.0"
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

??? "`pipeline.yaml`"

    ```yaml
      # StreamsApp component that configures a streams bootstrap app.
      # More documentation on StreamsApp: https://github.com/bakdata/streams-bootstrap
      - type: streams-app # required
        name: streams-app # required
        namespace: namespace # required
        # `app` can contain application-specific settings, hence  the user is free to
        # add the key-value pairs they need. The fields that are specific to streams
        # apps are marked with `# streams-app-specific`
        app: # required
          # Streams Bootstrap streams section
          streams: # required, streams-app-specific
            brokers: ${broker} # required
            schemaRegistryUrl: ${schema_registry_url}
            inputTopics:
              - "topic1"
              - "topic2"
            outputTopic: output-topic
            inputPattern: input-pattern
            extraInputTopics:
              input_role1:
                - input_topic1
                - input_topic2
              input_role2:
                - input_topic3
                - input_topic4
            extraInputPatterns:
              pattern_role1: input_pattern1
            extraOutputTopics: 
              output_role1: output_topic1
              output_role2: output_topic2
            errorTopic: error-topic
            config: 
              my.streams.config: my.value
          nameOverride: override-with-this-name # streams-app-specific
          autoscaling: # streams-app-specific
            consumergroup: consumer-group # required
            topics:
              - "topic1"
              - "topic2"
          key1:
            key4: value3
          key2: value1
          key3: value2
        # Topic(s) from which the component will read input
        from:
          topics: # required
            ${pipeline_name}-input-topic:
              type: input # required
              role: topic-role
        # Topic(s) into which the component will write output
        to:
          topics: # required
            ${pipeline_name}-output-topic:
              type: output # required
              role: topic-role
              keySchema: key-schema
              valueSchema: value-schema
              partitions_count: 1
              replication_factor: 1
              configs: 
                config1: config1
          models: 
            model: model
        # Pipeline prefix that will prefix every component name. If you wish to not 
        # have any prefix you can specify an empty string.
        prefix: ${pipeline_name}-
        # Helm repository configuration, the default value is given here
        repoConfig:
          repositoryName: bakdata-streams-bootstrap # required
          url: https://bakdata.github.io/streams-bootstrap/ # required
          repo_auth_flags:
            username: user
            password: pass
            ca_file: /home/user/path/to/ca-file
            insecure_skip_tls_verify: false
        version: "2.7.0"
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

??? "`pipeline.yaml`"

    ```yaml
      # Holds configuration to use as values for the streams bootstrap produce helm
      # chart.
      # More documentation on ProducersApp:
      # https://github.com/bakdata/streams-bootstrap
      - type: producer # required
        name: producer # required
        namespace: namespace # required
        # `app` can contain application-specific settings, hence  the user is free to
        # add the key-value pairs they need. The fields that are specific to producers
        # are marked with `# producer-specific`
        app: # required
          streams: # required, producer-specific
            brokers: ${broker} # required
            schemaRegistryUrl: ${schema_registry_url}
            outputTopic: output_topic
            extraOutputTopics: 
              output_role1: output_topic1
              output_role2: output_topic2
          nameOverride: override-with-this-name # kafka-app-specific
          kkey1:
            key4: value3
          key2: value1
          key3: value2
        # Topic(s) from which the component will read input
        from:
          topics: # required
            ${pipeline_name}-input-topic:
              type: input # required
              role: topic-role
        # Topic(s) into which the component will write output
        to:
          topics: # required
            ${pipeline_name}-output-topic:
              type: output # required
              role: topic-role
              keySchema: key-schema
              valueSchema: value-schema
              partitions_count: 1
              replication_factor: 1
              configs: 
                config1: config1
          models: 
            model: model
        # Pipeline prefix that will prefix every component name. If you wish to not 
        # have any prefix you can specify an empty string.
        prefix: ${pipeline_name}-
        # Helm repository configuration, the default value is given here
        repoConfig:
          repositoryName: bakdata-streams-bootstrap # required
          url: https://bakdata.github.io/streams-bootstrap/ # required
          repo_auth_flags:
            username: user
            password: pass
            ca_file: /home/user/path/to/ca-file
            insecure_skip_tls_verify: false
        version: "2.7.0"
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

??? "`pipeline.yaml`"

    ```yaml
      - type: kafka-sink-connector
        name: kafka-sink-connector # required
        namespace: namespace # required
        # `app` contains application-specific settings, hence it does not have a rigid
        # structure. The fields below are just an example.
        app: # required
          key1:
            key4: value3
          key2: value1
          key3: value2
        # Topic(s) from which the component will read input
        from:
          topics: # required
            ${pipeline_name}-input-topic:
              type: input # required
              role: topic-role
        # Topic(s) into which the component will write output
        to:
          topics: # required
            ${pipeline_name}-output-topic:
              type: output # required
              role: topic-role
              keySchema: key-schema
              valueSchema: value-schema
              partitions_count: 1
              replication_factor: 1
              configs: 
                config1: config1
          models: 
            model: model
        # Pipeline prefix that will prefix every component name. If you wish to not 
        # have any prefix you can specify an empty string.
        prefix: ${pipeline_name}-
        # Helm repository configuration
        repoConfig:
          repositoryName: my-repo # required
          url: https://bakdata.github.io/kafka-connect-resetter/ # required
          repoAuthFlags: 
            username: user
            password: pass
            ca_file: /home/user/path/to/ca-file
            insecure_skip_tls_verify: false
        version: "1.0.4"
        # Overriding Kafka Connect Resetter Helm values. E.g. to override the
        # Image Tag etc.
        resetterValues:
          imageTag: 1.2.3
        offsetTopic: offset_topic
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

??? "`pipeline.yaml`"

    ```yaml
      # Kafka source connector
      - type: kafka-source-connector
        name: kafka-source-connector # required
        namespace: namespace # required
        # `app` contains application-specific settings, hence it does not have a rigid
        # structure. The fields below are just an example.
        app: # required
          key1:
            key4: value3
          key2: value1
          key3: value2
        # Topic(s) from which the component will read input
        from:
          topics: # required
            ${pipeline_name}-input-topic:
              type: input # required
              role: topic-role
        # Topic(s) into which the component will write output
        to:
          topics: # required
            ${pipeline_name}-output-topic:
              type: output # required
              role: topic-role
              keySchema: key-schema
              valueSchema: value-schema
              partitions_count: 1
              replication_factor: 1
              configs: 
                config1: config1
          models: 
            model: model
        # Pipeline prefix that will prefix every component name. If you wish to not 
        # have any prefix you can specify an empty string.
        prefix: ${pipeline_name}-
        # Helm repository configuration
        repoConfig:
          repositoryName: my-repo # required
          url: https://bakdata.github.io/kafka-connect-resetter/ # required
          repoAuthFlags: 
            username: user
            password: pass
            ca_file: /home/user/path/to/ca-file
            insecure_skip_tls_verify: false
        version: "1.0.4"
        # Overriding Kafka Connect Resetter Helm values. E.g. to override the
        # Image Tag etc.
        resetterValues:
          imageTag: 1.2.3
        offsetTopic: offset_topic
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
