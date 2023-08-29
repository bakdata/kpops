# Editor integration

KPOps provides JSON schemas that enable autocompletion and validation for some of the files that the user must work with.

## Supported files

- [`pipeline.yaml`](../../resources/pipeline-components/pipeline.md)
- [`config.yaml`](../core-concepts/config.md)

## Usage

1. Install the [yaml-language-server](https://github.com/redhat-developer/yaml-language-server#clients){target=_blank} in your editor of choice. (requires LSP support)
2. Configure the extension with the settings below.

<!-- dprint-ignore-start -->

??? note "`settings.json`"

    ```json
    --8<--
    ./docs/resources/editor_integration/settings.json
    --8<--
    ```

!!! tip "Advanced usage"
    It is possible to generate schemas with the [`kpops schema`](./cli-commands.md#kpops-schema) command. Useful when using custom components or when using a pre-release version of KPOps.

<!-- dprint-ignore-end -->
