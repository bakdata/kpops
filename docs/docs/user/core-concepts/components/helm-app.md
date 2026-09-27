# HelmApp

### Usage

Can be used to deploy any app in Kubernetes using Helm, for example, a REST service that serves Kafka data.

### Configuration

<!-- dprint-ignore-start -->

??? example "`pipeline.yaml`"

    ```yaml
    --8<--
    ./docs/resources/pipeline-components/helm-app.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

### Operations

#### deploy

Identical to [HelmApp's `deploy`](helm-app.md#deploy).

#### destroy

Identical to [HelmApp's `destroy`](helm-app.md#deploy).

#### reset

Do nothing.

#### clean

Do nothing.
