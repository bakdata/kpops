# Environment variables

Environment variables can be set by using the [export](<https://www.unix.com/man-page/linux/1/export/>) command in Linux or the [set](<https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/set_1>) command in Windows.

> [!TIP]
>
> **dotenv files**
>
> KPOps currently supports `.env` files only for variables related to the [config](<https://bakdata.github.io/kpops/dev/user/core-concepts/config/index.md>). Full support for `.env` files is on the [roadmap](<https://github.com/bakdata/kpops/issues/20>). One of the possible ways to use one and export the contents manually is with the following command: `export $(xargs < .env)`. This would work in `bash` suppose there are no spaces inside the values.

## Config

These variables take precedence over the settings in `config.yaml`. Variables marked as required can instead be set in the global config.

| Name | Default Value | Required | Description | Setting name |
| --- | --- | --- | --- | --- |
| KPOPS\_PIPELINE\_BASE\_DIR | . | False | Base directory to the pipelines (default is current working directory) | pipeline\_base\_dir |
| KPOPS\_KAFKA\_BROKERS |  | True | The comma separated Kafka brokers address. | kafka\_brokers |
| KPOPS\_TOPIC\_NAME\_CONFIG\_\_DEFAULT\_OUTPUT\_TOPIC\_NAME | ${pipeline.name}-${component.name} | False | Configures the value for the variable ${output\_topic\_name} | topic\_name\_config.default\_output\_topic\_name |
| KPOPS\_TOPIC\_NAME\_CONFIG\_\_DEFAULT\_ERROR\_TOPIC\_NAME | ${pipeline.name}-${component.name}-error | False | Configures the value for the variable ${error\_topic\_name} | topic\_name\_config.default\_error\_topic\_name |
| KPOPS\_SCHEMA\_REGISTRY\_\_ENABLED | False | False | Whether the Schema Registry handler should be initialized. | schema\_registry.enabled |
| KPOPS\_SCHEMA\_REGISTRY\_\_URL | http://localhost:8081/ | False | Address of the Schema Registry. | schema\_registry.url |
| KPOPS\_SCHEMA\_REGISTRY\_\_TIMEOUT | 30 | False | Operation timeout in seconds. | schema\_registry.timeout |
| KPOPS\_KAFKA\_REST\_\_URL | http://localhost:8082/ | False | Address of the Kafka REST Proxy. | kafka\_rest.url |
| KPOPS\_KAFKA\_REST\_\_TIMEOUT | 30 | False | Operation timeout in seconds. | kafka\_rest.timeout |
| KPOPS\_KAFKA\_CONNECT\_\_URL | http://localhost:8083/ | False | Address of Kafka Connect. | kafka\_connect.url |
| KPOPS\_KAFKA\_CONNECT\_\_TIMEOUT | 30 | False | Operation timeout in seconds. | kafka\_connect.timeout |
| KPOPS\_CREATE\_NAMESPACE | False | False | Flag for `helm upgrade --install`. Create the release namespace if not present. | create\_namespace |
| KPOPS\_HELM\_CONFIG\_\_CONTEXT |  | False | Name of kubeconfig context (`--kube-context`) | helm\_config.context |
| KPOPS\_HELM\_CONFIG\_\_DEBUG | False | False | Run Helm in Debug mode | helm\_config.debug |
| KPOPS\_HELM\_CONFIG\_\_API\_VERSION |  | False | Kubernetes API version used for `Capabilities.APIVersions` | helm\_config.api\_version |
| KPOPS\_HELM\_CONFIG\_\_TIMEOUT |  | False | Helm flag --timeout. Duration to wait for any individual Kubernetes operation | helm\_config.timeout |
| KPOPS\_HELM\_CONFIG\_\_FORCE\_REPLACE | False | False | Helm flag --force-replace. Forces resource updates by replacement | helm\_config.force\_replace |
| KPOPS\_RETAIN\_CLEAN\_JOBS | False | False | Whether to retain clean up jobs in the cluster or uninstall the, after completion. | retain\_clean\_jobs |
| KPOPS\_STRIMZI\_TOPIC |  | False | Configuration for Strimzi Kafka Topics. | strimzi\_topic |
| KPOPS\_OPERATION\_MODE | managed | False | The operation mode of KPOps (managed, manifest, argo). | operation\_mode |

> [!NOTE]
>
> **config\_env\_vars.env**
>
> Exhaustive list of all config-related environment variables
>
> ```py
> # Global config environment variables
> #
> # The default setup is shown. These variables take precedence over the
> # settings in `config.yaml`. Variables marked as required can instead
> # be set in the global config.
> #
> # pipeline_base_dir
> # Base directory to the pipelines (default is current working
> # directory)
> KPOPS_PIPELINE_BASE_DIR=.
> # kafka_brokers
> # The comma separated Kafka brokers address.
> KPOPS_KAFKA_BROKERS # No default value, required
> # topic_name_config.default_output_topic_name
> # Configures the value for the variable ${output_topic_name}
> KPOPS_TOPIC_NAME_CONFIG__DEFAULT_OUTPUT_TOPIC_NAME=${pipeline.name}-${component.name}
> # topic_name_config.default_error_topic_name
> # Configures the value for the variable ${error_topic_name}
> KPOPS_TOPIC_NAME_CONFIG__DEFAULT_ERROR_TOPIC_NAME=${pipeline.name}-${component.name}-error
> # schema_registry.enabled
> # Whether the Schema Registry handler should be initialized.
> KPOPS_SCHEMA_REGISTRY__ENABLED=False
> # schema_registry.url
> # Address of the Schema Registry.
> KPOPS_SCHEMA_REGISTRY__URL=http://localhost:8081/
> # schema_registry.timeout
> # Operation timeout in seconds.
> KPOPS_SCHEMA_REGISTRY__TIMEOUT=30
> # kafka_rest.url
> # Address of the Kafka REST Proxy.
> KPOPS_KAFKA_REST__URL=http://localhost:8082/
> # kafka_rest.timeout
> # Operation timeout in seconds.
> KPOPS_KAFKA_REST__TIMEOUT=30
> # kafka_connect.url
> # Address of Kafka Connect.
> KPOPS_KAFKA_CONNECT__URL=http://localhost:8083/
> # kafka_connect.timeout
> # Operation timeout in seconds.
> KPOPS_KAFKA_CONNECT__TIMEOUT=30
> # create_namespace
> # Flag for `helm upgrade --install`. Create the release namespace if
> # not present.
> KPOPS_CREATE_NAMESPACE=False
> # helm_config.context
> # Name of kubeconfig context (`--kube-context`)
> KPOPS_HELM_CONFIG__CONTEXT # No default value, not required
> # helm_config.debug
> # Run Helm in Debug mode
> KPOPS_HELM_CONFIG__DEBUG=False
> # helm_config.api_version
> # Kubernetes API version used for `Capabilities.APIVersions`
> KPOPS_HELM_CONFIG__API_VERSION # No default value, not required
> # helm_config.timeout
> # Helm flag --timeout. Duration to wait for any individual Kubernetes
> # operation
> KPOPS_HELM_CONFIG__TIMEOUT # No default value, not required
> # helm_config.force_replace
> # Helm flag --force-replace. Forces resource updates by replacement
> KPOPS_HELM_CONFIG__FORCE_REPLACE=False
> # retain_clean_jobs
> # Whether to retain clean up jobs in the cluster or uninstall the,
> # after completion.
> KPOPS_RETAIN_CLEAN_JOBS=False
> # strimzi_topic
> # Configuration for Strimzi Kafka Topics.
> KPOPS_STRIMZI_TOPIC # No default value, not required
> # operation_mode
> # The operation mode of KPOps (managed, manifest, argo).
> KPOPS_OPERATION_MODE=managed
> ```

## CLI

These variables take precedence over the commands' flags. If a variable is set, the corresponding flag does not have to be specified in commands. Variables marked as required can instead be set as flags.

| Name | Default Value | Required | Description |
| --- | --- | --- | --- |
| KPOPS\_CONFIG\_PATH | . | False | Path to the dir containing config.yaml files |
| KPOPS\_DOTENV\_PATH |  | False | Path to dotenv file. Multiple files can be provided. The files will be loaded in order, with each file overriding the previous one. |
| KPOPS\_ENVIRONMENT |  | False | The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults\_development.yaml for environment=development). |
| KPOPS\_OPERATION\_MODE | managed | False | How KPOps should operate. |
| KPOPS\_PIPELINE\_PATHS |  | True | Paths to dir containing 'pipeline.yaml' or files named 'pipeline.yaml'. |
| KPOPS\_PIPELINE\_STEPS |  | False | Comma separated list of steps to apply the command on |

> [!NOTE]
>
> **cli\_env\_vars.env**
>
> Exhaustive list of all cli-related environment variables
>
> ```py
> # CLI Environment variables
> #
> # The default setup is shown. These variables take precedence over the
> # commands' flags. If a variable is set, the corresponding flag does
> # not have to be specified in commands. Variables marked as required
> # can instead be set as flags.
> #
> # Path to the dir containing config.yaml files
> KPOPS_CONFIG_PATH=.
> # Path to dotenv file. Multiple files can be provided. The files will
> # be loaded in order, with each file overriding the previous one.
> KPOPS_DOTENV_PATH # No default value, not required
> # The environment you want to generate and deploy the pipeline to.
> # Suffix your environment files with this value (e.g.
> # defaults_development.yaml for environment=development).
> KPOPS_ENVIRONMENT # No default value, not required
> # How KPOps should operate.
> KPOPS_OPERATION_MODE=managed
> # Paths to dir containing 'pipeline.yaml' or files named
> # 'pipeline.yaml'.
> KPOPS_PIPELINE_PATHS # No default value, required
> # Comma separated list of steps to apply the command on
> KPOPS_PIPELINE_STEPS # No default value, not required
> ```
