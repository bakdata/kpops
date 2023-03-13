# Editor integration

KPOps provides JSON schemas that enable autocompletion and validation for some of the files that the user must work with.

## Supported files

- [`pipeline.yaml`](/user/references/components){target=_blank}
- [`config.yaml`](/user/references/config){target=_blank}

## Usage

1. Install the
[yaml-language-server](https://github.com/redhat-developer/yaml-language-server#clients){target=_blank} in your editor of choice. (requires LSP support)
2. Configure the extension with the settings below.

???+ "`settings.json`"

    ```json
      --8<--
      ./docs/resources/editor_integration/settings.json
      --8<--
    ```
