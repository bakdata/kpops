# How to contribute

**Welcome!** We are glad to have you visit our contributing guide!

If you find any bugs or have suggestions for improvements, please open an [issue](https://github.com/bakdata/kpops/issues/new) and optionally a [pull request (PR)](https://github.com/bakdata/kpops/compare). In the case of a PR, we would appreciate it if you preface it with an issue outlining your goal and means of achieving it.

## Development setup

Install the dependencies using [mise-en-place](https://mise.jdx.dev/).

```sh
mise install
```

It will also install git commit hooks which are used for linting, type checking and to create the documentation.

### git

We are using [git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) to import the [KPOps examples](https://github.com/bakdata/kpops-examples) repository. You need to fetch the repository locally on your machine. To do so use this command:

```sh
git submodule init
git submodule update --recursive
```

This will fetch the resources under the `examples` folder.
