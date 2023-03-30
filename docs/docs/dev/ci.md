# CI

## Actions

### gen-docs

Generates and commits all files related to documentation. Commits with message "docs(cli): Autogenerate CLI Usage page".

#### Prerequisites

-

#### Input Parameters

| Name              | Required | Default Value | Description                                            |
| ----------------- | :------: | :-----------: | ------------------------------------------------------ |
| username          |    ✅    |       -       | The GitHub username for committing the changes         |
| email             |    ✅    |       -       | The GitHub email for committing the changes            |
| token             |    ✅    |       -       | The GitHub token for committing the changes            |
| python-version    |    ✅    |       -       | The Python version for the Poetry virtual environment. |
| poetry-version    |    ✅    |       -       | The Poetry version to be installed.                    |
| just-version      |    ✅    |       -       | The Just version to be used for running the generation |

#### Usage

```yaml
{% raw %}
steps:
  - name: Generate CLI Usage page
    uses: ./.github/actions/gen-docs
      with:
        username: ${{ secrets.GH_USERNAME }}
        email: ${{ secrets.GH_EMAIL }}
        token: ${{ secrets.GH_TOKEN }}
        python-version: "3.10"
        poetry-version: "1.3.2"
        just-version: "1.4.0"
{% endraw %}
```

### update-docs

## Workflows

### add-isue-ci.yaml

### ci.yaml

### publish-test-pypi.yaml

### release.yaml
