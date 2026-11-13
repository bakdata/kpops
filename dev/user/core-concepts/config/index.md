# Configuration

KPOps reads its global configuration that is unrelated to a pipeline's [components](<https://bakdata.github.io/kpops/dev/user/core-concepts/components/overview/index.md>) from [`config.yaml`](<#__codelineno-0-1>).

Consider enabling [KPOps' editor integration](<https://bakdata.github.io/kpops/dev/user/references/editor-integration/index.md>) feature to enjoy the benefits of autocompletion and validation when configuring your pipeline.

To learn about any of the available settings, take a look at the example below.

> [!NOTE]
>
> **`config.yaml`**
>
> ```yaml
> # CONFIGURATION
> #
> # Base directory to the pipelines (default is current working directory)
> pipeline_base_dir: .
> # The Kafka brokers address.
> # REQUIRED
> kafka_brokers: "http://broker1:9092,http://broker2:9092"
> # Configure the topic name variables you can use in the pipeline definition.
> topic_name_config:
>   # Configures the value for the variable ${output_topic_name}
>   default_output_topic_name: ${pipeline.name}-${component.name}
>   # Configures the value for the variable ${error_topic_name}
>   default_error_topic_name: ${pipeline.name}-${component.name}-error
> # Configuration for Schema Registry.
> schema_registry:
>   # Whether the Schema Registry handler should be initialized.
>   enabled: false
>   # Address of the Schema Registry.
>   url: "http://localhost:8081"
> # Configuration for the Kafka REST Proxy.
> kafka_rest:
>   # Address of the Kafka REST Proxy.
>   url: "http://localhost:8082"
> # Configuration for Kafka Connect.
> kafka_connect:
>   # Address of Kafka Connect.
>   url: "http://localhost:8083"
> # Flag for `helm upgrade --install`.
> # Create the release namespace if not present.
> create_namespace: false
> # Global flags for Helm.
> helm_config:
>   # Name of kubeconfig context (`--kube-context`)
>   context: name
>   # Run Helm in Debug mode.
>   debug: false
>   # Kubernetes API version used for Capabilities.APIVersions
>   api_version: null
> # Whether to retain clean up jobs in the cluster or uninstall the, after
> # completion.
> retain_clean_jobs: false
> ```

> [!NOTE]
>
> **Environment-specific pipeline definitions**
>
> Similarly to [defaults](<https://bakdata.github.io/kpops/dev/user/core-concepts/defaults/index.md#configuration>), it is possible to have an unlimited amount of additional environment-specific pipeline definitions. The naming convention is the same: add a suffix of the form `_{environment}` to the filename.
