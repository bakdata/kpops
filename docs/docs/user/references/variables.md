# Variables

KPOps makes use of various variables to improve the user's experience.

## Substitution

The [pipeline](components.md) definition and its [defaults](defaults.md) allow usage of placeholders and environment.

### Component-specific variables

These variables can be used in a component's definition to refer to any of its attributes, including ones that the user has defined in the defaults.

All of them are prefixed with `component_` and follow the following form: `component_{attribute_name}`. If the attribute itself contains attributes, they can be referred to like this: `component_{attribute_name}_{subattribute_name}`.

??? Example
    ```yaml
      --8<--
      ./docs/resources/variables/variable_substitution.yaml
      --8<--
    ```

### Pipeline-config-specific variables

These variables include all fields in the [config](config.md) and refer to the pipeline configuration that is independent of the components.

### Environment variables

Environment variables such as `$PATH` can be used in the pipeline definition and defaults without any transformation following the form `${ENV_VAR_NAME}`. This, of course includes variables like the ones relevant to the [KPOps cli](cli-commands.md) that are exported by the user.

### Advanced use cases

1. Refer to default component field values
As long as a value is assigned to a component attribute, it is possible to refer to it with a placeholder. To see all component fields, take a look at the [pipeline schema](../../schema/pipeline.json).
2. Chaining vars
It is possible to chain any number of variables, see the example below.

    ```yaml
        var0: key
        var1: value
        var2: ${var1} # var2: value
        var3: ${var2} # var3: value
        ${var0}: ${var3} # key: value
    ```

3. Cross-component substitution
[YAML](https://yaml.org/) is quite an intricate language and with some of its [magic](https://yaml.org/spec/1.2.2/#692-node-anchors) one could write cross-component references.

### Pipeline name variables

These are special variables that refer to the name and path of a pipeline.

- `${pipeline_name}`: Concatenated path of the parent directory where pipeline.yaml is defined in.
  For instance, `/data/pipelines/v1/pipeline.yaml`, here the value for the variable would be `data-pipelines-v1`.
- `${pipeline_name_<level>}`: Similar to the previous variable, each `<level>` contains a part of the path to the
  `pipeline.yaml` file. Consider the previous example, `${pipeline_name_0}` would be `data`,
  `${pipeline_name_1}` would be `pipelines`, and `${pipeline_name_2}` equals to `v1`.

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

1. Config-related
2. CLI-related
