# Editor integration

## Native

We are working towards first-class editor support by providing plugins that work out of the box.

- Neovim: [kpops.nvim](<https://github.com/disrupted/kpops.nvim>)
- Visual Studio Code: *planned*

## Manual (for unsupported editors with LSP)

1. Install the [yaml-language-server](<https://github.com/redhat-developer/yaml-language-server#clients>) in your editor of choice. (requires LSP support)
2. Configure the extension with the settings below.

> [!NOTE]
>
> **`settings.json`**
>
> ```json
> {
>     "yaml.schemas": {
>         "https://bakdata.github.io/kpops/4.0/schema/pipeline.json": [
>             "pipeline.yaml",
>             "pipeline_*.yaml"
>         ],
>         "https://bakdata.github.io/kpops/4.0/schema/defaults.json": [
>             "defaults.yaml",
>             "defaults_*.yaml"
>         ],
>         "https://bakdata.github.io/kpops/4.0/schema/config.json": [
>             "config.yaml",
>             "config_*.yaml"
>         ]
>     }
> }
> ```

> [!TIP]
>
> **Advanced usage**
>
> It is possible to generate schemas with the [`kpops schema`](<https://bakdata.github.io/kpops/dev/user/references/cli-commands/index.md#kpops-schema>) command. Useful for including custom components or when using a pre-release version of KPOps.

---

## Concepts

KPOps provides JSON schemas that enable autocompletion and validation for all YAML files that the user must work with.

### Supported files

- [`pipeline.yaml`](<https://bakdata.github.io/kpops/dev/resources/pipeline-components/pipeline/index.md>)
- [`defaults.yaml`](<https://bakdata.github.io/kpops/dev/user/core-concepts/defaults/index.md>)
- [`config.yaml`](<https://bakdata.github.io/kpops/dev/user/core-concepts/config/index.md>)
