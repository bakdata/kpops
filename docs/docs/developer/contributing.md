# How to contribute

**Welcome!** We are glad to have you visit our contributing guide!

If you find any bugs or have suggestions for improvements, please open an [issue](https://github.com/bakdata/kpops/issues/new) and optionally a [pull request (PR)](https://github.com/bakdata/kpops/compare). In the case of a PR, we would appreciate it if you preface it with an issue outlining your goal and means of achieving it.

### git

We are using [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) to import the [KPOps examples](https://github.com/bakdata/kpops-examples) repository. You need to fetch the repository locally on your machine. To do so use this command:

```bash
git submodule init
git submodule update --recursive
```

This will fetch the resources under the `examples` folder.

## Style

We advise that you stick to our `pre-commit` hooks for code linting, formatting, and auto-generation of documentation. After you install them using `pre-commit install` they're triggered automatically during `git commit`. Additionally, you can manually invoke them with `pre-commit run -a`. In order for `dprint` to work, you have to manually [install](#markdown) it locally. It will work in the CI, so it is also possible to manually carry out formatting changes flagged by `dprint` in the CI and skip installing it locally.

### Python

To ensure a consistent Python code style, we use [Ruff](https://docs.astral.sh/ruff/) for both linting and formatting. The official docs contain a guide on [editor integration](https://docs.astral.sh/ruff/integrations/).

Our configuration can be found in [KPOps](https://github.com/bakdata/kpops)' top-level `pyproject.toml`.

### Markdown

To ensure a consistent markdown style, we use [dprint](https://dprint.dev)'s [Markdown code formatter](https://dprint.dev/plugins/markdown/). Our configuration can be found [here](https://github.com/bakdata/kpops/blob/main/dprint.json).

### CSS

To ensure a consistent CSS style, we use the [malva](https://github.com/g-plane/malva) [dprint](https://dprint.dev)'s plugin. Our configuration can be found [here](https://github.com/bakdata/kpops/blob/main/dprint.json).

### TOML

To ensure a consistent TOML style, we use [dprint](https://dprint.dev)'s [TOML code formatter](https://dprint.dev/plugins/toml/). Our configuration can be found [here](https://github.com/bakdata/kpops/blob/main/dprint.json).
