# Style

## Python

To ensure a consistent Python code style, we use [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting.

### Configuration

Our configuration can be found in [KPOps](https://github.com/bakdata/kpops)' top-level `pyproject.toml`.

### Editor integration

Below are listed existing Ruff plugins/extensions for some of the most popular python IDEs. If you cannot find your Editor of choices or you want something more custom, [`ruff-lsp`](https://github.com/astral-sh/ruff-lsp) enables Ruff to be used in any editor that supports the LSP

- [VSCode](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
- [PyCharm](https://plugins.jetbrains.com/plugin/20574-ruff)

## Markdown

To ensure a consistent markdown style, we use [dprint](https://dprint.dev) to check and reformat.

```shell
dprint fmt
```

Use the [official documentation](https://dprint.dev/setup/) to set up dprint.
The configuration can be found [here](https://github.com/bakdata/kpops/blob/main/dprint.json).
