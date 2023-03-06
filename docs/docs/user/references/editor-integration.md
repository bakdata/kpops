# Editor integration

KPOps provides JSON schemas that enable autocompletion and validation for some of the files that the user must work with.

## Supported files

- [`pipeline.yaml`](/user/references/components)
- [`config.yaml`](/user/references/config)

## Usage

1. Install the
[yaml-language-server](https://github.com/redhat-developer/yaml-language-server#clients) in your editor of choice. (requires LSP support)
2. Configure the extension with the settings below.

???+ "`settings.json`"

    ```json
      --8<--
      ./docs/resources/editor_integration/settings.json
      --8<--
    ```

!!! bug
    Currently there is a [bug](https://github.com/redhat-developer/vscode-yaml/issues/523) in VScode's [Yaml Language Support](https://github.com/redhat-developer/vscode-yaml/) extension that gives an error when having both local (path) and remote (URI) schemas that match a file.
