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
| kpops-version     |    ❌     |    latest     | string | KPOps version to install                                                                                                                      |
| helm-version      |    ❌     |    latest     | string | Helm version to install                                                                                                                       |
| token             |    ❌     |    latest     | string | secrets.GITHUB_TOKEN, needed for setup-helm action if helm-version is set to latest                                                           |
| python-version    |    ❌     |   "3.11.x"    | string | Python version to install (Defaults to the latest stable version of Python 3.11)                                                              |

## Usage

```yaml
steps:
  - name: Deploy Kafka pipeline
    uses: bakdata/kpops/actions/kpops-runner@main
    with:
      command: deploy --execute
      working-directory: home/my-kpops-root-dir
      pipeline: pipelines/my-pipeline-file.yaml
      kpops-version: 1.1.2
```
