# Substitution

KPOps supports the usage of placeholders and environment variables in [pipeline definition](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/overview/index.md>) and [defaults](<https://bakdata.github.io/kpops/dev/user/core-concepts/defaults/index.md>).

## Component-specific variables

These variables can be used in a component's definition to refer to any of its attributes, including ones that the user has defined in the defaults.

All of them are prefixed with `component.` and follow the following form: `component.{attribute_name}`. If the attribute itself contains attributes, they can be referred to like this: `component.{attribute_name}.{subattribute_name}`.

> [!NOTE]
>
> **Example**
>
> ```yaml
> - type: scheduled-producer
>   values:
>     labels:
>       app_type: "${component.type}"
>       app_name: "${component.name}"
>       app_schedule: "${component.values.schedule}"
>     commandLine:
>       FAKE_ARG: "fake-arg-value"
>     schedule: "30 3/8 * * *"
> - type: converter
>   values:
>     commandLine:
>       CONVERT_XML: true
>     resources:
>       limits:
>         memory: 2G
>       requests:
>         memory: 2G
> - type: filter
>   name: "filter-app"
>   values:
>     labels:
>       app_type: "${component.type}"
>       app_name: "${component.name}"
>       app_resources_requests_memory: "${component.values.resources.requests.memory}"
>       ${component.type}: "${component.values.labels.app_name}-${component.values.labels.app_type}"
>       test_placeholder_in_placeholder: "${component.values.labels.${component.type}}"
>     commandLine:
>       TYPE: "nothing"
>     resources:
>       requests:
>         memory: 3G
>     replicaCount: 4
>     autoscaling:
>       minReplicas: 4
>       maxReplicas: 4
> ```

## Pipeline-config-specific variables

These variables include all fields in the [config](<https://bakdata.github.io/kpops/dev/user/core-concepts/config/index.md>) and refer to the pipeline configuration that is independent of the components.

All such variables are prefixed with `config.` and are of the same form as the [component-specific variables](<#component-specific-variables>).

> [!NOTE]
>
> **Info**
>
> `error_topic_name` is an alias for `config.topic_name_config.default_error_topic_name`  
> `output_topic_name` is an alias for `config.topic_name_config.default_output_topic_name`

## Environment variables

Environment variables such as `$PATH` can be used in the pipeline definition and defaults without any transformation following the form `${ENV_VAR_NAME}`. This, of course, includes variables like the ones relevant to the [KPOps cli](<https://bakdata.github.io/kpops/dev/user/references/cli-commands/index.md>) that are exported by the user.

[See all KPOps environment variables](<https://bakdata.github.io/kpops/dev/user/core-concepts/variables/environment_variables/index.md>)

## Pipeline name variables

These are special variables that refer to the name and path of a pipeline.

- `${pipeline.name}`: Concatenated path of the directory that contains the file pipeline.yaml. For instance, `./data/pipelines/v1/pipeline.yaml`, here the value for the variable would be `data-pipelines-v1`.

- `${pipeline_name_<level>}`: Similar to the previous variable, each `<level>` contains a part of the path to the `pipeline.yaml` file. Consider the previous example, `${pipeline_name_0}` would be `data`, `${pipeline_name_1}` would be `pipelines`, and `${pipeline_name_2}` equals to `v1`.

- `${pipeline.parent.name}`: Like `${pipeline.name}` but only up to the *parent directory* of the directory that contains the file pipeline.yaml. For instance, `./data/pipelines/v1/pipeline.yaml`, here the value for the variable would be `data-pipelines`. This can be useful e.g. to read from a component of a pipeline defined in `./data/pipelines/pipeline.yaml` (without `/v1`).

## Advanced use cases

1. **Refer to default component field values**: As long as a value is assigned to a component attribute, it is possible to refer to it with a placeholder. To see all component fields, take a look at the [pipeline schema](<https://bakdata.github.io/kpops/dev/schema/pipeline.json>).
2. **Chaining variables**: It is possible to chain any number of variables, see the [example](<#component-specific-variables>) above.
3. **Cross-component substitution**: [YAML](<https://yaml.org/>) is quite an intricate language and with some of its [magic](<https://yaml.org/spec/1.2.2/#692-node-anchors>) one could write cross-component references.
