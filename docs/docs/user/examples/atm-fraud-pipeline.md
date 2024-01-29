# ATM fraud detection pipeline

ATM fraud is a demo pipeline for ATM fraud detection.
The original by Confluent is written in KSQL
and outlined in this [blogpost](https://www.confluent.io/blog/atm-fraud-detection-apache-kafka-ksql/){target=_blank}.
The one used in this example is re-built from scratch using [bakdata](https://bakdata.com/){target=_blank}'s
[`streams-bootstrap`](https://github.com/bakdata/streams-bootstrap){target=_blank} library.

## What this will demonstrate

- Deploying a PostgreSQL database using Helm
- Deploying a pipeline using KPOps
- Destroying a pipeline using KPOps

## Prerequisites

Completed all steps in the [setup](../getting-started/setup.md).

## Setup and deployment

### PostgreSQL

Deploy PostgreSQL using the [Bitnami Helm chart:](https://artifacthub.io/packages/helm/bitnami/postgresql){target=_blank}
Add the helm repository:

```shell
helm repo add bitnami https://charts.bitnami.com/bitnami && \
helm repo update
```

Install the PostgreSQL with helm:

```shell
helm upgrade --install -f ./postgresql.yaml \
--namespace kpops \
postgresql bitnami/postgresql
```

<!-- dprint-ignore-start -->

??? example "PostgreSQL Example Helm chart values (`postgresql.yaml`)"
    ```yaml
    auth:
      database: app_db
      enablePostgresUser: true
      password: AppPassword
      postgresPassword: StrongPassword
      username: app1
    primary:
      persistence:
        enabled: false
        existingClaim: postgresql-data-claim
    volumePermissions:
      enabled: true
    ```

<!-- dprint-ignore-end -->

### ATM fraud detection example pipeline setup

#### Port forwarding

Before we deploy the pipeline, we need to forward the ports of `kafka-rest-proxy` and `kafka-connect`. Run the following commands in two different terminals.

```shell
kubectl port-forward --namespace kpops service/k8kafka-cp-rest 8082:8082
```

```shell
kubectl port-forward --namespace kpops service/k8kafka-cp-kafka-connect 8083:8083
```

### Deploying the ATM fraud detection pipeline

<!-- dprint-ignore-start -->

1. Clone the [kpops-examples repository](https://github.com/bakdata/kpops-examples){target=_blank} and `cd` into the directory.

2. Install KPOps `pip install -r requirements.txt`.

3. Export environment variables in your terminal:

    ```shell
    export DOCKER_REGISTRY=bakdata && \
    export NAMESPACE=kpops
    ```

4. Deploy the pipeline

    ```shell
    kpops deploy atm-fraud/pipeline.yaml --execute
    ```

!!! Note
    You can use the `--dry-run` flag instead of the `--execute` flag and check the logs if your pipeline will be
    deployed correctly.

<!-- dprint-ignore-end -->

### Check if the deployment is successful

You can use the [Streams Explorer](https://github.com/bakdata/streams-explorer){target=_blank} to see the deployed pipeline.
To do so, port-forward the service in a separate terminal session using the command below:

```shell
kubectl port-forward -n kpops service/streams-explorer 8080:8080
```

After that open [http://localhost:8080](http://localhost:8080){target=_blank} in your browser.
You should be able to see pipeline shown in the image below:

<figure markdown>
  ![atm-fraud-pipeline](../../images/atm-fraud-pipeline_streams-explorer.png)
  <figcaption>An overview of ATM fraud pipeline shown in Streams Explorer</figcaption>
</figure>

<!-- dprint-ignore-start -->

!!! Attention
    Kafka Connect needs some time to set up the connector.
    Moreover, Streams Explorer needs a while to scrape the information from Kafka connect.
    Therefore, it might take a bit until you see the whole graph.

<!-- dprint-ignore-end -->

## Teardown resources

### PostrgreSQL

PostgreSQL can be uninstalled by running the following command:

```shell
helm --namespace kpops uninstall postgresql
```

### ATM fraud pipeline

<!-- dprint-ignore-start -->

1. Export environment variables in your terminal.

    ```shell
    export DOCKER_REGISTRY=bakdata && \
    export NAMESPACE=kpops
    ```

2. Remove the pipeline

    ```shell
    kpops clean atm-fraud/pipeline.yaml --verbose  --execute
    ```

!!! Note
    You can use the `--dry-run` flag instead of the `--execute` flag and check the logs if your pipeline will be
    destroyed correctly.

!!! Attention
    If you face any issues destroying this example see [Teardown](../getting-started/teardown.md) for manual deletion.

<!-- dprint-ignore-end -->

## Common errors

- `deploy` fails:
  1. Read the error message.
  2. Try to correct the mistakes if there were any. Likely the configuration is incorrect, or the port-forwarding is not working as intended.
  3. Run `clean`.
  4. Run `deploy --dry-run` to avoid havig to `clean` again. If an error is dropped, start over from step 1.
  5. If the dry-run is succesful, run `deploy`.
- `clean` fails:
  1. Read the error message.
  2. Try to correct the indicated mistakes if there were any. Likely the configuration is incorrect, or the port-forwarding is not working as intended.
  3. Run `clean`.
  4. If `clean` fails, follow the steps in [teardown](../getting-started/teardown.md).
