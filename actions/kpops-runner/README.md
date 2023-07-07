# KPOps runner

This action runs KPOps with the given config.

## Input Parameters

| Name              | Required | Default Value |  Type  | Description                                                                                                                                   |
|-------------------|:--------:|:-------------:|:------:|-----------------------------------------------------------------------------------------------------------------------------------------------|
| command           |    ✅     |       -       | string | KPOps command to run. generate, deploy, destroy, reset, clean are possible values. Flags such as --dry-run and --execute need to be specified |
| pipeline          |    ✅     |       -       | string | Pipeline to run by KPOps                                                                                                                      |
| working-directory |    ❌     |       .       | string | root directory used by KPOps to run pipelines                                                                                                 |
| pipeline-base-dir |    ❌     |       .       | string | directory where relative pipeline variables are initialized from                                                                              |
| defaults          |    ❌     |       .       | string | defaults folder path                                                                                                                          |
| config            |    ❌     |  config.yaml  | string | config.yaml file path                                                                                                                         |
| components        |    ❌     |       -       | string | components package path                                                                                                                       |
| python-version    |    ❌     |   "3.11.x"    | string | Python version to install (Defaults to the latest stable version of Python 3.11)                                                              |
| kpops-version     |    ❌     |    latest     | string | KPOps version to install                                                                                                                      |
| helm-version      |    ❌     |    latest     | string | Helm version to install                                                                                                                       |
| token             |    ❌     |    latest     | string | secrets.GITHUB_TOKEN, needed for setup-helm action if helm-version is set to latest                                                           |

## Usage

```yaml
steps:
  - name: Deploy Kafka pipeline
    uses: bakdata/kpops/actions/kpops-runner@main
    with:
      command: deploy --execute
      working-directory: home/my-kpops-root-dir
      pipeline: pipelines/my-pipeline-file.yaml
      kpops-version: 1.2.3
```

It is possible to execute the KPOps runner on
a dev version from the [test.pypi](https://test.pypi.org/project/kpops/#history).

```yaml
steps:
  - name: Deploy Kafka pipeline
    uses: bakdata/kpops/actions/kpops-runner@main
    with:
      command: deploy --execute
      working-directory: home/my-kpops-root-dir
      pipeline: pipelines/my-pipeline-file.yaml
      kpops-version: 1.2.5.dev20230707132709 -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/
```
