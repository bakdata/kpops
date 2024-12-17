# Operation Modes in KPOps

KPOps supports three operation modes—`managed`, `manifest`, and `argo`. These modes determine how resources are managed and allow users to tailor their deployment strategy.

- **Managed Mode** (default): KPOps uses Helm, and communicates with services like Kafka Rest Proxy, and Kafka Connect under the hood to manage the installation/(graceful) deletion of applications, creation/deletion of Kafka topics, creation/deletion of Connectors defined in your `pipeline.yaml`.
- **Manifest Mode**: Focuses on generating Kubernetes manifests.
- **Argo Mode**: Extends the functionality to include ArgoCD-specific hooks for certain operations, facilitating GitOps workflows with automated cleanup and reset tasks.

---

## Configuring Operation Modes

It is possible to configure the operation mode in the `config.yaml` file. Please refer to the [Configuration documentation page](https://bakdata.github.io/kpops/9.0/user/core-concepts/config/).
Alternatively, you can to pass the `--operation-mode <OPERATION>` option in the CLI to override the operation mode of the `config.yaml`. You can refer to the [CLI commands documentation](https://bakdata.github.io/kpops/9.0/user/references/cli-commands/#kpops-deploy) for more details.

---

## Generated Resources by Mode and Operation

### `deploy`

#### **Manifest Mode**

- **streams-bootstrap Applications**:
  - Depending on your pipeline configuration, Kubernetes `Job`, `Deployment`, `ConfigMap`, and `Service` resources.
  - Please refer to [Streams-bootstrap Helm Charts](https://github.com/bakdata/streams-bootstrap/tree/master/charts).
- **Topics**:
  - Strimzi `KafkaTopic` CRDs.

#### **Argo Mode**

- **streams-bootstrap Applications**:
  - Depending on your pipeline configuration, Kubernetes `Job`, `Deployment`, `ConfigMap`, and `Service` resources.
  - Additional `sync-wave` annotation with value of `>0` to prioritizes Kafka Topics deployment over the application
  - Please refer to [Streams-bootstrap Helm Charts](https://github.com/bakdata/streams-bootstrap/tree/master/charts).
- **Topics**:
  - Strimzi `KafkaTopic` CRDs.
- **Cleanup Jobs**:
  - Kubernetes `Job` resources configured **with** ArgoCD `PostDelete` hooks, ensuring cleanup tasks are executed after ArgoCD application deletion.

---

### `reset`

#### **Manifest Mode**

- **Topics**:
  - Strimzi `KafkaTopic` CRDs.
- **Reset Jobs**:
  - Kubernetes `Job` resources for resetting Kafka Streams application states.

#### **Argo Mode**

- **Topics**:
  - Strimzi `KafkaTopic` CRDs.
- **Reset Jobs**:
  - Kubernetes `Job` resources **without** ArgoCD `PostDelete` hooks, providing a simpler reset process.

---

### `clean`

#### **Manifest Mode**

- **Clean Jobs**:
  - Kubernetes `Job` resources for cleaning up temporary resources or artifacts using application container images.

#### **Argo Mode**

- **Not Applicable**:
  - The `clean` command is not supported in Argo mode. The clean can be achieved through manifesting hooked cleanup jobs during the `deploy` command.

---

### `destroy`

#### **Manifest Mode**

- **Topics**:
  - Strimzi `KafkaTopic` CRDs.

#### **Argo Mode**

- **Topics**:
  - Strimzi `KafkaTopic` CRDs.

---

## Use Cases for Each Mode

### Manifest Mode

- **Flexibility**: Use the generated manifests in manual workflows or integrate with any Kubernetes deployment tool.
- **Version Control**: Commit generated manifests to a Git repository for tracking changes and rollback.

### Argo Mode

- **GitOps Integration**: Simplifies workflows when using ArgoCD for automated deployments and lifecycle management.
- **PostDelete Hooks**: Automatically cleans up resources after deletion of ArgoCD applications.

---

## Summary of Resource Generation by Operation and Mode

| Resource Type | `deploy`                         | `reset`             | `clean`             | `destroy`           |
| ------------- | -------------------------------- | ------------------- | ------------------- | ------------------- |
| Producer Apps | Manifest: Generated              | N/A                 | N/A                 | N/A                 |
|               | Argo: Generated                  |                     |                     |                     |
| Streams Apps  | Manifest: Generated              | N/A                 | N/A                 | N/A                 |
|               | Argo: Generated                  |                     |                     |                     |
| Topics        | Manifest: Generated              | Manifest: Generated | N/A                 | Manifest: Generated |
|               | Argo: Generated                  | Argo: Generated     |                     | Argo: Generated     |
| Cleanup Jobs  | Manifest: N/A                    | N/A                 | Manifest: Generated | N/A                 |
|               | Argo: With `PostDelete` hooks    | N/A                 | N/A                 | N/A                 |
| Reset Jobs    | Manifest: N/A                    | Manifest: Generated | N/A                 | N/A                 |
|               | Argo: Without `PostDelete` hooks |                     |                     |                     |
