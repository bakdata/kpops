# KPOps

[![Latest release](https://img.shields.io/github/v/release/bakdata/kpops)](https://github.com/bakdata/kpops/releases/latest)
[![Build status](https://github.com/bakdata/kpops/actions/workflows/ci.yaml/badge.svg)](https://github.com/bakdata/kpops/actions/workflows/ci.yaml)

For detailed usage and installation instructions, check out
the [documentation](https://bakdata.github.io/kpops/latest).

## Features

- **Deploy Kafka apps to Kubernetes**: KPOps allows to deploy consecutive Kafka Streams applications, producers, and Kafka connectors using an easy-to-read and write pipeline definition. 
- **Configure multiple pipelines and steps**: KPOps comes with various abstractions that simplify configuring multiple pipelines and steps within pipelines by sharing configuration between different applications, like producers or streaming applications.
- **Customize your components**: KPOps comes with multiple base components (Kafka connect, producer, etc.) and allows you to introduce custom components.
- **Handle your topics and schemas**: KPOps not only creates and deletes your topics but also registers and deletes your schemas.
- **Manage the lifecycle of your components**: KPOps can deploy, destroy, reset, and clean your defined components from the Kubernetes cluster.

## Install KPOps

KPOps comes as a [PyPI package](https://pypi.org/project/kpops/). 
You can install it with [pip](https://github.com/pypa/pip):

```shell
pip install kpops
```

## Documentation

- [What is KPOps?](https://bakdata.github.io/kpops/latest/user)
- [Getting started with KPOps](https://bakdata.github.io/kpops/latest/user/getting-started/)
- [Examples](https://bakdata.github.io/kpops/latest/user/examples)

## Contributing

We are happy if you want to contribute to this project.
If you find any bugs or have suggestions for improvements, please open an issue.
We are also happy to accept your PRs.
Just open an issue beforehand and let us know what you want to do and why.

## License

KPOps is licensed under the [MIT License](https://github.com/bakdata/kpops/blob/main/LICENSE).
