# Editor integration

## Native

We are working towards first-class editor support by providing plugins that work out of the box.

- Neovim: [kpops.nvim](https://github.com/disrupted/kpops.nvim)
- Visual Studio Code: _planned_

## Manual (for unsupported editors with LSP)

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
    It is possible to generate schemas with the [`kpops schema`](./cli-commands.md#kpops-schema) command. Useful for including custom components or when using a pre-release version of KPOps.

<!-- dprint-ignore-end -->

---

## Concepts

KPOps provides JSON schemas that enable autocompletion and validation for all YAML files that the user must work with.

### Supported files

- [`pipeline.yaml`](../../resources/pipeline-components/pipeline.md)
- [`defaults.yaml`](../core-concepts/defaults.md)
- [`config.yaml`](../core-concepts/config.md)
