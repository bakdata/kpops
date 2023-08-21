## KubernetesApp

### Usage

Can be used to deploy any app in Kubernetes using Helm, for example, a REST service that serves Kafka data.

### Configuration

??? example "`pipeline.yaml`"

    ```yaml
      --8<--
      ./docs/resources/pipeline-components/kubernetes-app.yaml
      --8<--
    ```

### Operations

#### deploy

Deploy using Helm.

#### destroy

Uninstall Helm release.

#### reset

Do nothing.

#### clean

Do nothing.
