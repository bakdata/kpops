# Variables

## Pipeline variables

- `${pipeline_name}`: Concatenated path of the parent directory where pipeline.yaml is defined in.
  For instance, `/data/pipelines/v1/pipeline.yaml`, here the value for the variable would be `data-pipelines-v1`.
- `${pipeline_name_<level>}`: Similar to the previous variable, each `<level>` contains a part of the path to the
  `pipeline.yaml` file. Consider the previous example, `${pipeline_name_0}` would be `data`,
  `${pipeline_name_1}` would be `pipelines`, and `${pipeline_name_2}` equals to `v1`.

## Component specific variables

- `${component_type}`: The type of the component
- `${component_name}`: The name of the component

Topic names depending on the component:

- `${topic_name}`: You can define the value using the `config.yaml` and the
  field: `topic_name_config.default_output_topic_name`
- `${error_topic_name}`: You can define the value using the `config.yaml` and the
  field: `topic_name_config.default_error_topic_name`

An example for the content of the `config.yaml` to define your project-specific topic names is:

```yaml
topic_name_config:
  default_error_topic_name: "${pipeline_name}-${component_type}-error-topic"
  default_output_topic_name: "${pipeline_name}-${component_type}-topic"
```

## Environment Variables

| Variable                  | Required         | Default Value | Description                                           |
| :------------------------ | :--------------- | :------------ | :---------------------------------------------------- |
| `KPOPS_PIPELINE_PATH`     | :material-check: |               | Path to YAML with pipeline definition                 |
| `KPOPS_PIPELINE_BASE_DIR` | :material-close: | `.`           | Base directory to the pipelines                       |
| `KPOPS_DEFAULT_PATH`      | :material-close: | `defaults`    | Path to defaults folder                               |
| `KPOPS_CONFIG_PATH`       | :material-close: | `config.yaml` | Path to the config.yaml file                          |
| `KPOPS_PIPELINE_STEPS`    | :material-close: | `None`        | Comma separated list of steps to apply the command on |
