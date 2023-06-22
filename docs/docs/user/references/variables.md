# Variables

KPOps makes use of various variables to improve the user's experience.

## Substitution

The [pipeline](components.md) definition and its [defaults](defaults.md) allow usage of placeholders and environment.

### Component-specific variables

These variables can be used in a component's definition to refer to any of its attributes, including ones that the user has defined in the defaults.

All of them are prefixed with `component_` and follow the following form: `component_{attribute_name}`. If the attribute itself contains attributes, they can be referred to like so: `component_{attribute_name}_{subattribute_name}`.

??? Example
    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kubernetes-app.yaml
      --8<--
    ```

### Pipeline-config-specific variables

These variables refer to the pipeline configuration that is independent of the components. These include all fields in the [config](config.md)

- `${pipeline_name}`: Concatenated path of the parent directory where pipeline.yaml is defined in.
  For instance, `/data/pipelines/v1/pipeline.yaml`, here the value for the variable would be `data-pipelines-v1`.
- `${pipeline_name_<level>}`: Similar to the previous variable, each `<level>` contains a part of the path to the
  `pipeline.yaml` file. Consider the previous example, `${pipeline_name_0}` would be `data`,
  `${pipeline_name_1}` would be `pipelines`, and `${pipeline_name_2}` equals to `v1`.

### Environment variables

1. Existing
2. Create your own

### Advanced use cases

1. Default fields - look at the schema
2. Chaining vars
3. Cross-component substitution

### Pipeline variables



### Component specific variables

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

## Environment variables

### CLI commands
Some variables can be used as a more permanent way to set options for the CLI commands. For those, please refer to the [CLI Usage](cli-commands.md) page.

1. The pipeline config file does not support variable substitution currently.
2. The following settings can be set as env vars:
