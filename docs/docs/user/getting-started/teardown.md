# Teardown resources

## KPOps teardown commands

- `destroy`: Removes Kubernetes resources.
- `reset`: Runs `destroy`, resets the states of Kafka Streams apps and resets offsets to zero.
- `clean`: Runs `reset` and removes all Kafka resources.

## KPOps-deployed pipeline

The [`kpops` CLI](../references/cli-commands.md) can be used to destroy a pipeline that was previously deployed with KPOps.
In case that doesn't work, the pipeline can always be taken down manually with `helm` (see section [Infrastructure](#infrastructure)).

<!-- dprint-ignore-start -->

1. Export environment variables.

    ```shell
    export DOCKER_REGISTRY=bakdata && \
    export NAMESPACE=kpops
    ```

2. Navigate to the `examples` folder.
    Replace the `<name-of-the-example-directory>` with the example you want to tear down.
    For example the `atm-fraud-detection`.

3. Remove the pipeline

    ```shell
    # Uncomment 1 line to either destroy, reset or clean.

    # kpops destroy <name-of-the-example-directory>/pipeline.yaml \
    # kpops reset <name-of-the-example-directory>/pipeline.yaml \
    # kpops clean <name-of-the-example-directory>/pipeline.yaml \
    --config <name-of-the-example-directory>/config.yaml \
    --execute
    ```

<!-- dprint-ignore-end -->

## Infrastructure

Delete namespace:

```shell
kubectl delete namespace kpops
```

<!-- dprint-ignore-start -->

!!! Note
    In case `kpops destroy` is not working one can uninstall the pipeline services one by one.
    This is equivalent to running `kpops destroy`. In case a clean uninstall (like the one `kpops clean` does) 
    is needed, one needs to also delete the topics and schemas created by deployment of the pipeline.

<!-- dprint-ignore-end -->

## Local cluster

Delete local cluster:

```shell
k3d cluster delete kpops
```

## Local image registry

Delete local registry:

```shell
k3d registry delete k3d-kpops-registry.localhost
```
