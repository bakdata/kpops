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

We advise that you stick to our Git hooks for code linting, formatting, and auto-generation of documentation. After you install them using `lefthook install` they're triggered automatically during `git` operations, such as commit or checkout. Additionally, you can manually invoke them with `lefthook run pre-commit --all-files`. Please also install the [`dprint`](https://dprint.dev/) formatter.
