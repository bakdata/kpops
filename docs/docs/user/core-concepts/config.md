# Configuration

KPOps reads its global configuration that is unrelated to a pipeline's [components](./components/overview.md) from [`config.yaml`](#__codelineno-0-1).

Consider enabling [KPOps' editor integration](../references/editor-integration.md) feature to enjoy the benefits of autocompletion and validation when configuring your pipeline.

To learn about any of the available settings, take a look at the example below.

<!-- dprint-ignore-start -->

??? example "`config.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-config/config.yaml
    --8<--
    ```

!!! note "Environment-specific pipeline definitions"
    Similarly to [defaults](defaults.md#configuration), it is possible to have an unlimited amount of additional environment-specific pipeline definitions. The naming convention is the same: add a suffix of the form `_{environment}` to the filename.

<!-- dprint-ignore-end -->
