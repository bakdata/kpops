# What is KPOps?

With a couple of easy commands in the shell, and a [`pipeline.yaml`](<#example>) of under 30 lines, KPOps can not only [`deploy`](<https://bakdata.github.io/kpops/dev/user/references/cli-commands/index.md#kpops-deploy>) a Kafka pipeline[^/kpops/dev/user/what-is-kpops/#1] to a Kubernetes cluster, but also [`reset`](<https://bakdata.github.io/kpops/dev/user/references/cli-commands/index.md#kpops-reset>), [`clean`](<https://bakdata.github.io/kpops/dev/user/references/cli-commands/index.md#kpops-clean>) or [`destroy`](<https://bakdata.github.io/kpops/dev/user/references/cli-commands/index.md#kpops-destroy>) it!

> [!TIP]
>
> **Working with AI agents**
>
> Point your agent to [`llms.txt`](<https://bakdata.github.io/kpops/llms.txt>), e.g. to write pipelines or migrate a project to a new major version.

## Key features

- **Deploy Kafka apps to Kubernetes**: KPOps allows to deploy consecutive Kafka Streams applications and producers using an easy-to-read and -write pipeline definition.
- **Manage Kafka Connectors**: KPOps connects with your Kafka Connect cluster and deploys, validates, and deletes your connectors.
- **Configure multiple pipelines and steps**: KPOps has various abstractions that simplify configuring multiple pipelines and steps within pipelines by sharing common configuration between different components, such as producers or streaming applications.
- **Handle your topics and schemas**: KPOps not only creates and deletes your topics but also registers and deletes your schemas.
- **Clean termination of Kafka components**: KPOps removes your pipeline components (i.e., Kafka Streams applications) from the Kubernetes cluster *and* cleans up the component-related states (i.e., removing/resetting offset of Kafka consumer groups).
- **Preview your pipeline changes**: With the KPOps dry-run, you can ensure your pipeline definition is set up correctly. This helps to minimize downtime and prevent potential errors or issues that could impact your production environment.

## Example

[![atm-fraud-pipeline](<https://bakdata.github.io/kpops/dev/images/word-count-pipeline_streams-explorer.png>)](<https://bakdata.github.io/kpops/dev/images/word-count-pipeline_streams-explorer.png>)

An overview of [Word-count pipeline](<https://bakdata.github.io/kpops/dev/getting-started/quick-start>) shown in [Streams Explorer](<https://github.com/bakdata/streams-explorer#streams-explorer>)

Word-count pipeline.yaml

```yaml
- type: producer-app
  name: data-producer
  values:
    image: bakdata/kpops-demo-sentence-producer

- type: streams-app
  name: word-count-app
  values:
    image: bakdata/kpops-demo-word-count-app
    replicaCount: 1
  to:
    topics:
      ${output_topic_name}:
        type: output
        configs:
          cleanup.policy: compact

- type: kafka-sink-connector
  name: redis-sink-connector
  config:
    connector.class: com.github.jcustenborder.kafka.connect.redis.RedisSinkConnector
    redis.hosts: redis-headless:6379
    redis.database: 0
    tasks.max: 1
    key.converter: org.apache.kafka.connect.storage.StringConverter
    value.converter: org.apache.kafka.connect.storage.StringConverter
```

[^/kpops/dev/user/what-is-kpops/#1]: A Kafka pipeline can consist of consecutive [streaming applications](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/streams-app/index.md>), [producers](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/producer-app/index.md>), and [connectors](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/kafka-connector/index.md>).
