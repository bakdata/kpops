# Contributions

**Welcome!** We are glad to have you visit our contributibg guide!

If you find any bugs or have suggestions for improvements, please open an [issue](https://github.com/bakdata/kpops/issues/new) and optionally a [pull request (PR)](https://github.com/bakdata/kpops/compare). In the case of a PR, we would appreciate it if you preface it with an issue outlining your goal and means of achieving it.

## Style

We advise that you stick to our `pre-commit` hooks, which you can run with `poetry run pre-commit run -a`. In order for `dprint` to work, you have to manually [install](#markdown) it locally. It will work in the CI, so it is also possible to manually carry out formatting changes flagged by `dprint` in the CI and skip installing it locally.

### Python

To ensure a consistent Python code style, we use [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting.

**Configuration**

Our configuration can be found in [KPOps](https://github.com/bakdata/kpops)' top-level `pyproject.toml`.

**Editor integration**

Below are listed existing Ruff plugins/extensions for some of the most popular python IDEs.

- [VSCode](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)
- [JetBrains](https://plugins.jetbrains.com/plugin/20574-ruff)

If you cannot find your Editor of choices or you want something more custom, [`ruff-lsp`](https://github.com/astral-sh/ruff-lsp) enables Ruff to be used in any editor that supports the LSP

### Markdown

To ensure a consistent markdown style, we use [dprint](https://dprint.dev)'s [Markdown code formatter](https://dprint.dev/plugins/markdown/).

**Configuration**

Our configuration can be found [here](https://github.com/bakdata/kpops/blob/main/dprint.json).

**Editor integration**

Below are listed existing `dprint` plugins/extensions for some of the most popular python IDEs.

- [VSCode](https://marketplace.visualstudio.com/items?itemName=dprint.dprint)
- [JetBrains](https://plugins.jetbrains.com/plugin/18192-dprint)
