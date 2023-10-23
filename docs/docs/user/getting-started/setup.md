# Setup KPOps

In this part, you will set up KPOps. This includes:

- optionally creating a local Kubernetes cluster
- running Apache Kafka and Confluent's Schema Registry
- installing KPOps

## Prerequisites

- [k3d (Version 5.4.6+)](https://k3d.io/v5.4.6/){target=_blank} and [Docker (Version >= v20.10.5)](https://www.docker.com/get-started/){target=_blank} or an existing Kubernetes cluster (>= 1.21.0)
- [kubectl (Compatible with server version 1.21.0)](https://kubernetes.io/docs/tasks/tools/){target=_blank}
- [Helm (Version 3.8.0+)](https://helm.sh){target=_blank}

## Setup Kubernetes with k3d

<!-- dprint-ignore-start -->

If you don't have access to an existing Kubernetes cluster, this section will guide you through creating a local cluster. We recommend the lightweight Kubernetes distribution [k3s](https://k3s.io/){target=_blank} for this. [k3d](https://k3d.io/){target=_blank} is a wrapper around k3s in Docker that lets you get started fast.


1. You can install k3d with its installation script:

    ```shell
    wget -q -O - https://raw.githubusercontent.com/k3d-io/k3d/v5.4.6/install.sh | bash
    ```

    For other ways of installing k3d, you can have a look at their [installation guide](https://k3d.io/v5.4.6/#installation){target=_blank}.

2. The [Kafka deployment](#deploy-kafka) needs a modified Docker image. In that case the image is built and pushed to a Docker registry that holds it. If you do not have access to an existing Docker registry, you can use k3d's Docker registry:

    ```shell
    k3d registry create kpops-registry.localhost --port 12345
    ```

3. Now you can create a new cluster called `kpops` that uses the previously created Docker registry:

    ```shell
    k3d cluster create kpops --k3s-arg "--no-deploy=traefik@server:*" --registry-use k3d-kpops-registry.localhost:12345
    ```

!!! Note
    Creating a new k3d cluster automatically configures `kubectl` to connect to the local cluster by modifying your `~/.kube/config`. In case you manually set the `KUBECONFIG` variable or don't want k3d to modify your config, k3d offers [many other options](https://k3d.io/v5.4.6/usage/kubeconfig/#handling-kubeconfigs){target=_blank}.

<!-- dprint-ignore-end -->

You can check the cluster status with `kubectl get pods -n kube-system`. If all returned elements have a `STATUS` of `Running` or `Completed`, then the cluster is up and running.

## Deploy Kafka

<!-- dprint-ignore-start -->

[Kafka](https://kafka.apache.org/){target=_blank} is an open-source data streaming platform. More information about Kafka can be found in the [documentation](https://kafka.apache.org/documentation/){target=_blank}. To deploy Kafka, this guide uses Confluent's [Helm chart](https://github.com/confluentinc/cp-helm-charts){target=_blank}.

1. To allow connectivity to other systems [Kafka Connect](https://docs.confluent.io/platform/current/connect/index.html#kafka-connect){target=_blank} needs to be extended with drivers. You can install a [JDBC driver](https://docs.confluent.io/kafka-connectors/jdbc/current/jdbc-drivers.html){target=_blank} for Kafka Connect by creating a new Docker image:

    1. Create a `Dockerfile` with the following content:

        ```dockerfile
        FROM confluentinc/cp-kafka-connect:7.1.3

        RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:10.6.0
        ```

    2. Build and push the modified image to your private Docker registry:

        ```shell
        docker build . --tag localhost:12345/kafka-connect-jdbc:7.1.3 && \
        docker push localhost:12345/kafka-connect-jdbc:7.1.3
        ```

    Detailed instructions on building, tagging and pushing a docker image can be found in [Docker docs](https://docs.docker.com/){target=_blank}.

2. Add Confluent's Helm chart repository and update the index:

    ```shell
    helm repo add confluentinc https://confluentinc.github.io/cp-helm-charts/ &&  
    helm repo update
    ```

3. Install Kafka, Zookeeper, Confluent's Schema Registry, Kafka Rest Proxy, and Kafka Connect. A single Helm chart installs all five components. Below you can find an example for the `--values ./kafka.yaml` file configuring the deployment accordingly. Deploy the services:

    ```shell
    helm upgrade \
        --install \
        --version 0.6.1 \
        --values ./kafka.yaml \
        --namespace kpops \
        --create-namespace \
        --wait \
        k8kafka confluentinc/cp-helm-charts
    ```

??? example "Kafka Helm chart values (`kafka.yaml`)"
    An example value configuration for Confluent's Helm chart. This configuration deploys a single Kafka Broker, a Schema Registry, Zookeeper, Kafka Rest Proxy, and Kafka Connect with minimal resources.

    ```yaml
    --8<--
    ./docs/resources/setup/kafka.yaml
    --8<--
    ```

<!-- dprint-ignore-end -->

## Deploy Streams Explorer

[Streams Explorer](https://github.com/bakdata/streams-explorer){target=_blank} allows examining Apache Kafka data pipelines in a Kubernetes cluster including the inspection of schemas and monitoring of metrics. First, add the Helm repository:

```shell
helm repo add streams-explorer https://bakdata.github.io/streams-explorer && \
helm repo update
```

Below you can find an example for the `--values ./streams-explorer.yaml` file configuring the deployment accordingly. Now, deploy the service:

```shell
helm upgrade \
    --install \
    --version 0.2.3 \
    --values ./streams-explorer.yaml \
    --namespace kpops \
    streams-explorer streams-explorer/streams-explorer
```

<!-- dprint-ignore-start -->

??? example "Streams Explorer Helm chart values (`streams-explorer.yaml`)"
    An example value configuration for Steams Explorer Helm chart.

    ```yaml
    imageTag: "v2.1.2"
    config:
       K8S__deployment__cluster: true
       SCHEMAREGISTRY__url: http://k8kafka-cp-schema-registry.kpops.svc.cluster.local:8081
       KAFKACONNECT__url: http://k8kafka-cp-kafka-connect.kpops.svc.cluster.local:8083
    resources:
       requests:
           cpu: 200m
           memory: 300Mi
       limits:
           cpu: 200m
           memory: 300Mi
    ```

<!-- dprint-ignore-end -->

## Check the status of your deployments

Now we will check if all the pods are running in our namespace. You can list all pods in the namespace with this command:

```shell
kubectl --namespace kpops get pods
```

Then you should see the following output in your terminal:

```shell
NAME                                          READY   STATUS    RESTARTS   AGE
k8kafka-cp-kafka-connect-8fc7d544f-8pjnt      1/1     Running   0          15m
k8kafka-cp-zookeeper-0                        1/1     Running   0          15m
k8kafka-cp-kafka-0                            1/1     Running   0          15m
k8kafka-cp-schema-registry-588f8c65db-jdwbq   1/1     Running   0          15m
k8kafka-cp-rest-6bbfd7b645-nwkf8              1/1     Running   0          15m
streams-explorer-54db878c67-s8wbz             1/1     Running   0          15m
```

Pay attention to the `STATUS` row. The pods should have a status of `Running`.

## Install KPOps

KPOps comes as a [PyPI package](https://pypi.org/project/kpops/){target=_blank}. You can install it with `pip`:

```shell
pip install kpops
```
