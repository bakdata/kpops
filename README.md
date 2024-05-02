# KPOps

[![Build status](https://github.com/bakdata/kpops/actions/workflows/ci.yaml/badge.svg)](https://github.com/bakdata/kpops/actions/workflows/ci.yaml)
[![pypi](https://img.shields.io/pypi/v/kpops.svg)](https://pypi.org/project/kpops)
[![versions](https://img.shields.io/pypi/pyversions/kpops.svg)](https://github.com/bakdata/kpops)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![license](https://img.shields.io/github/license/bakdata/kpops.svg)](https://github.com/bakdata/kpops/blob/main/LICENSE)

## Key features

- **Deploy Kafka apps to Kubernetes**: KPOps allows to deploy consecutive Kafka Streams applications and producers using an easy-to-read and -write pipeline definition.
- **Manage Kafka Connectors**: KPOps connects with your Kafka Connect cluster and deploys, validates, and deletes your connectors.
- **Configure multiple pipelines and steps**: KPOps has various abstractions that simplify configuring multiple pipelines and steps within pipelines by sharing common configuration between different components, such as producers or streaming applications.
- **Handle your topics and schemas**: KPOps not only creates and deletes your topics but also registers and deletes your schemas.
- **Clean termination of Kafka components**: KPOps removes your pipeline components (i.e., Kafka Streams applications) from the Kubernetes cluster _and_ cleans up the component-related states (i.e., removing/resetting offset of Kafka consumer groups).
- **Preview your pipeline changes**: With the KPOps dry-run, you can ensure your pipeline definition is set up correctly. This helps to minimize downtime and prevent potential errors or issues that could impact your production environment.

## Documentation

For detailed usage and installation instructions, check out
the [documentation](https://bakdata.github.io/kpops/latest).

## Install KPOps

KPOps comes as a [PyPI package](https://pypi.org/project/kpops/).
You can install it with [pip](https://github.com/pypa/pip):

```sh
pip install kpops
```

# GitHub action

Please refer to the [GitHub Actions section](https://bakdata.github.io/kpops/latest/user/references/ci-integration/github-actions) for the documentation.

## Contributing

We are happy if you want to contribute to this project.
If you find any bugs or have suggestions for improvements, please open an issue.
We are also happy to accept your PRs.
Just open an issue beforehand and let us know what you want to do and why.

## License

KPOps is licensed under the [MIT License](https://github.com/bakdata/kpops/blob/main/LICENSE).
