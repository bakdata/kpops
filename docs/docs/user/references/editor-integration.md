# Editor integration

Kpops currently provides JSON schemas for the structure of `pipeline.yaml` and
`config.yaml`. The schemas can be utilized by any editor that implements the
[yaml-language-server](https://github.com/redhat-developer/yaml-language-server).

For a list of the more known editors that support the feature
[click here](https://microsoft.github.io/language-server-protocol/implementors/tools/).

To use the schemas, paste the code below into your editor's settings.

??? "`settings.json`"

    ```json
      --8<--
      ./docs/resources/editor_integration/settings.json
      --8<--
    ```
