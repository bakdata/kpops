# What is KPOps?

With a couple easy commands in the shell and a [`pipeline.yaml`](#example) of under 30 lines, [KPOps](/) can not only [`deploy`](../references/cli-commands/#deploy) a pipeline[^1] to a Kubernetes cluster, but also [`reset`](../references/cli-commands/#reset), [`clean`](../references/cli-commands/#clean) or [`destroy`](../references/cli-commands/#destroy) it!
[^1]:
     A pipeline can consist of just consecutive [Kafka Streams applications](../references/components/#streamsapp) or it could also contain [Producers](../references/components/#producer) and/or [Kafka Connectors](../references/defaults/#kafkaconnector).

## Key features

- Deploy pipelines with minimal effort and without sacrificing configurability
- Easy-to-read and write pipeline definitions
- Reset or destroy pipelines gracefully
- Reset or clean apps again with a single command
- Set defaults to share settings between pipeline steps (or whole different pipelines!)

## Example

<figure markdown>
  ![atm-fraud-pipeline](../images/word-count-pipeline_streams-explorer.png)
  <figcaption>An overview of <a href="../getting-started/quick-start">Word-count pipeline</a> shown in <a href="https://github.com/bakdata/streams-explorer#streams-explorer" target="_blank">Streams Explorer</a></figcaption>
</figure>

```yaml title="Word-count pipeline.yaml"
    --8<--
    https://raw.githubusercontent.com/bakdata/kpops-examples/main/word-count/deployment/kpops/pipeline.yaml
    --8<--
```
