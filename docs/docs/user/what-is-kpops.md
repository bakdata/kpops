# What is KPOps?

With a couple easy commands in the shell and a [`pipeline.yaml`](#example) of under 30 lines, [KPOps](/) can [`destroy`](/user/references/cli-commands/#deploy), [`reset`](/user/references/cli-commands/#reset), [`clean`](/user/references/cli-commands/#clean) or [`deploy`](/user/references/cli-commands/#deploy) a pipeline[^1] to a Kubernetes cluster!
[^1]:
     A pipeline can consist of just consecutive [Kafka Streams applications](/user/references/components/#streamsapp) or it could also contain [Producers](/user/references/components/#producer) and/or [Kafka Connectors](/user/references/defaults/#kafkaconnector).

## Key features

- Deploy pipelines with minimal effort and without sacrificing configurability
- Easy-to-read and write pipeline definitions
- Reset or destroy pipelines gracefully
- Reset or clean apps again with a single command
- Set defaults to share settings between pipeline steps (or whole different pipelines!)

## Example

```yaml title="Word-count pipeline.yaml"
    --8<--
    https://raw.githubusercontent.com/bakdata/kpops-examples/main/word-count/deployment/kpops/pipeline.yaml
    --8<--
```
