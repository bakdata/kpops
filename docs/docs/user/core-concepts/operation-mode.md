# Operation Modes in KPOps

KPOps supports three operation modes—`managed`, `manifest`, and `argo`. These modes determine how resources are managed and allow users to tailor their deployment strategy.

- **Managed Mode** (default): KPOps uses Helm, and communicates with services like Kafka Rest Proxy, and Kafka Connect under the hood to manage the installation/(graceful) deletion of applications, creation/deletion of Kafka topics, creation/deletion of Connectors defined in your `pipeline.yaml`.
- **Manifest Mode**: Focuses on generating Kubernetes manifests.
- **Argo Mode**: Extends the functionality to include ArgoCD-specific hooks for certain operations, facilitating GitOps workflows with automated cleanup and reset tasks.

---

## Configuring Operation Modes

You can configure the operation mode using one of the following methods:

1. **Command-Line Option**: Pass the `--operation-mode <OPERATION>` flag when running a CLI command. Refer to the [CLI commands documentation](https://bakdata.github.io/kpops/9.0/user/references/cli-commands/#kpops-deploy) for more details.

2. **Environment Variable**: Set the operation mode by defining the `KPOPS_OPERATION_MODE` environment variable.

---

## Generated Resources by Mode and Operation

### `deploy`

#### **Manifest Mode**

- **streams-bootstrap Applications**:
  - Depending on your pipeline configuration, Kubernetes `Job`, `Deployment`, `ConfigMap`, and `Service` resources.
  - Please refer to [streams-bootstrap Helm Charts](https://github.com/bakdata/streams-bootstrap/tree/master/charts).
- **Topics**:
  - Strimzi `KafkaTopic` CRDs.

#### **Argo Mode**

- **streams-bootstrap Applications**:
  - Depending on your pipeline configuration, Kubernetes `Job`, `Deployment`, `ConfigMap`, and `Service` resources.
  - Additional Argo `sync-wave` annotation to ensure Kafka topics are created first (default `sync-wave=0`) before deploying apps (lower priority `sync-wave>0`). All components of each sync wave are deployed in parallel by Argo.
  - Please refer to [streams-bootstrap Helm Charts](https://github.com/bakdata/streams-bootstrap/tree/master/charts).
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
  - The `clean` command is not supported in Argo mode. The clean is instead achieved through cleanup job hooks during the `deploy` command.

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
