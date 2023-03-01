# Editor integration

KPOps provides JSON schemas that enable autocompletion and validation for some
of the files that the user must work with.

## Supported files

- [`pipeline.yaml`](/user/references/components)
- [`config.yaml`](/user/references/config)

## Usage

1. Check that your editor implements the
[yaml-language-server](https://github.com/redhat-developer/yaml-language-server#clients)
2. Make sure to install the needed extension/plugin
3. Add the text below to your editor's settings.

??? "`settings.json`"

    ```json
      --8<--
      ./docs/resources/editor_integration/settings.json
      --8<--
    ```
