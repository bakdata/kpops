# HelmApp

### Usage

Can be used to deploy any app in Kubernetes using Helm, for example, a REST service that serves Kafka data.

`HelmApp` has no `from` or `to` section. To connect a Helm-based component to Kafka topics, create a custom component that combines `HelmApp` with the `ConsumesTopics` and `ProducesTopics` capabilities. See the [migration guide](<https://bakdata.github.io/kpops/dev/user/migration-guide/v12-v13/index.md>).

### Configuration

> [!NOTE]
>
> **`pipeline.yaml`**
>
> ```yaml
> # Kubernetes app managed through Helm with an associated Helm chart
> - type: helm-app
>   name: helm-app # required
>   # Pipeline prefix that will prefix every component name. If you wish to not
>   # have any prefix you can specify an empty string.
>   prefix: ${pipeline.name}-
>   namespace: namespace # required
>   values: # required
>     image: exampleImage # Example
>     debug: false # Example
>     commandLine: {} # Example
>   # Helm repository configuration (optional)
>   # If not set the helm repo add will not be called. Useful when using local Helm charts
>   repo_config:
>     repository_name: bakdata-streams-bootstrap # required
>     url: https://bakdata.github.io/streams-bootstrap/ # required
>     repo_auth_flags:
>       username: user
>       password: pass
>       ca_file: /home/user/path/to/ca-file
>       insecure_skip_tls_verify: false
>   version: "1.0.0" # Helm chart version
> ```

### Operations

#### deploy

Identical to [HelmApp's `deploy`](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/helm-app/index.md#deploy>).

#### destroy

Identical to [HelmApp's `destroy`](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/helm-app/index.md#deploy>).

#### reset

Do nothing.

#### clean

Do nothing.
