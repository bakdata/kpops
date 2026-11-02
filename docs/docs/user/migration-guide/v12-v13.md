# Migrate from V12 to V13

## Python 3.14+ required

KPOps v13 supports only Python 3.14 and 3.15. Upgrade your Python environment before upgrading KPOps.

## `from` and `to` removed from `helm-app` and `kubernetes-app`

`helm-app` and `kubernetes-app` no longer accept the `from` and `to` sections. Previously, `from` had no effect and `to` only wired the next component of the pipeline.

If you need topic support for a Helm-based component, define a custom component that combines the capabilities `ConsumesTopics` and `ProducesTopics` with `HelmApp`:

```python
from kpops.components.base_components import ConsumesTopics, HelmApp, ProducesTopics


class MyKafkaHelmApp(ConsumesTopics, ProducesTopics, HelmApp): ...
```

The component must implement the topic hooks (`add_input_topics`, `set_output_topic`, …) to map topics into its Helm values.

## Unsupported sections are rejected

Components that do not support the `from` or `to` section now fail validation with a clear error instead of silently ignoring the section:

- `from` on `producer-app` and `kafka-source-connector`
- `to` on `consumer-app`
- `from` and `to` on `helm-app` and `kubernetes-app`

This also applies to values merged in from the `defaults.yaml` of shared keys such as `pipeline-component`.

## Kafka connectors inherit `kafka-app` defaults

Kafka connectors are now `KafkaApp`s. Settings defined under `kafka-app` in `defaults.yaml` now also apply to `kafka-connector`, `kafka-source-connector` and `kafka-sink-connector`.

## Defaults schema

`from` and `to` are no longer offered under `pipeline-component`, `kubernetes-app`, `helm-app`, `kafka-app` and `streams-bootstrap` in `defaults.yaml` (and `from` under `kafka-connector`). Define them under the concrete component keys instead.

#### defaults.yaml

```diff
- kafka-app:
-   to:
-     ...
+ streams-app:
+   to:
+     ...
```

## Custom components (Python API)

- `PipelineComponent.supports_from_section()` has been removed. Use `isinstance(component, ConsumesTopics)` instead.
- The topic hooks moved from `PipelineComponent` to the capability classes `ConsumesTopics` (input) and `ProducesTopics` (output).
- `KubernetesApp`, `HelmApp` and `StreamsBootstrap` are generic over their values type:

```diff
- class MyApp(HelmApp):
+ class MyApp(HelmApp[MyValues]):
      values: MyValues
```

- Custom intermediate base classes that are later combined with a built-in app (diamond inheritance, e.g. `class MyProducer(ProducerApp, MyStreamsBootstrapBase)`) should become generic too. Otherwise type checkers report inconsistent type arguments.

```python
class MyStreamsBootstrapBase[V: StreamsBootstrapValues[Any] = StreamsBootstrapValues](
    StreamsBootstrap[V]
): ...


class MyProducer(ProducerApp, MyStreamsBootstrapBase[ProducerAppValues]): ...
```

This replaces former `# pyright: ignore[reportIncompatibleVariableOverride]` workarounds.

- `ConsumerAppValues` gained the generic base `BaseConsumerAppValues[K]`.
- `StreamsBootstrap.repo_config` and `StreamsBootstrap.version` are now typed as optional.
