# GitHub Actions integration

We provided a GitHub composite action `bakdata/kpops` that installs and executes KPOps commands with the given parameters.

## Input Parameters

| Name              | Required | Default Value |  Type  | Description                                                                                                                                   |
| ----------------- | :------: | :-----------: | :----: | --------------------------------------------------------------------------------------------------------------------------------------------- |
| command           |    ✅    |       -       | string | KPOps command to run. generate, deploy, destroy, reset, clean are possible values. Flags such as --dry-run and --execute need to be specified |
| pipeline          |    ✅    |       -       | string | Pipeline to run by KPOps                                                                                                                      |
| working-directory |    ❌    |       .       | string | root directory used by KPOps to run pipelines                                                                                                 |
| defaults          |    ❌    |       -       | string | defaults folder path                                                                                                                          |
| config            |    ❌    |       -       | string | Directory containing the config*.yaml file path                                                                                               |
| environment       |    ❌    |       -       | string | Environment to run KPOps in                                                                                                                   |
| components        |    ❌    |       -       | string | components package path                                                                                                                       |
| filter-type       |    ❌    |       -       | string | Whether to include/exclude the steps defined in KPOPS_PIPELINE_STEPS                                                                          |
| python-version    |    ❌    |   "3.11.x"    | string | Python version to install (Defaults to the latest stable version of Python 3.11)                                                              |
| kpops-version     |    ❌    |    latest     | string | KPOps version to install                                                                                                                      |
| helm-version      |    ❌    |    latest     | string | Helm version to install                                                                                                                       |
| token             |    ❌    |    latest     | string | secrets.GITHUB_TOKEN, needed for setup-helm action if helm-version is set to latest                                                           |

## Usage

```yaml
steps:
  # ...
  # This step is useful for debugging reasons
  - name: Generate Kafka pipeline
    uses: bakdata/kpops@main
    with:
      command: generate
      working-directory: home/my-kpops-root-dir
      pipeline: pipelines/my-pipeline-file.yaml
      kpops-version: 1.2.3

  - name: Deploy Kafka pipeline
    uses: bakdata/kpops@main
    with:
      command: deploy --execute
      working-directory: home/my-kpops-root-dir
      pipeline: pipelines/my-pipeline-file.yaml
      kpops-version: 1.2.3
  # ...
```

It is possible to use a pre-release KPOps version from [TestPyPI](https://test.pypi.org/project/kpops/#history).

```yaml
steps:
  - name: Deploy Kafka pipeline
    uses: bakdata/kpops@main
    with:
      command: deploy --execute
      working-directory: home/my-kpops-root-dir
      pipeline: pipelines/my-pipeline-file.yaml
      kpops-version: 1.2.5.dev20230707132709 -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
```
