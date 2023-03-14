# What is KPOps?

With a couple of easy commands in the shell and a [`pipeline.yaml`](#example) of under 30 lines, [KPOps](/) can not only [`deploy`](/user/references/cli-commands/#deploy) a Kafka pipeline[^1] to a Kubernetes cluster, but also [`reset`](/user/references/cli-commands/#reset), [`clean`](/user/references/cli-commands/#clean) or [`destroy`](/user/references/cli-commands/#destroy) it!
[^1]:
     A Kafka pipeline can consist of consecutive [streaming applications](/user/references/components/#streamsapp), [producers](/user/references/components/#producer), and [connectors](/user/references/defaults/#kafkaconnector).

## Key features

- Easy-to-read and write pipeline definitions
- Deploy pipelines with minimal effort and without sacrificing configurability
- Reset or destroy pipelines gracefully
- Reset or clean apps again with a single command
- Set [defaults](/user/references/defaults) to share settings within and across pipelines

## Example

<figure markdown>
  ![atm-fraud-pipeline](/images/word-count-pipeline_streams-explorer.png)
  <figcaption>An overview of <a href="/user/getting-started/quick-start">Word-count pipeline</a> shown in <a href="https://github.com/bakdata/streams-explorer#streams-explorer" target="_blank">Streams Explorer</a></figcaption>
</figure>

```yaml title="Word-count pipeline.yaml"
    --8<--
    https://raw.githubusercontent.com/bakdata/kpops-examples/main/word-count/deployment/kpops/pipeline.yaml
    --8<--
```
