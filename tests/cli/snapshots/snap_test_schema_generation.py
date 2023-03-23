# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestGenSchema.test_gen_config_schema test-schema-generation"] = {
    "$ref": "#/definitions/PipelineConfig",
    "definitions": {
        "HelmConfig": {
            "properties": {
                "context": {
                    "description": "Set the name of the kubeconfig context. (--kube-context)",
                    "example": "dev-storage",
                    "title": "Context",
                    "type": "string",
                },
                "debug": {
                    "default": False,
                    "description": "Run Helm in Debug mode.",
                    "title": "Debug",
                    "type": "boolean",
                },
            },
            "title": "HelmConfig",
            "type": "object",
        },
        "HelmDiffConfig": {
            "properties": {
                "enable": {
                    "default": True,
                    "description": "Enable Helm Diff.",
                    "title": "Enable",
                    "type": "boolean",
                },
                "ignore": {
                    "description": "Set of keys that should not be checked.",
                    "example": """- name
- imageTag""",
                    "items": {"type": "string"},
                    "title": "Ignore",
                    "type": "array",
                    "uniqueItems": True,
                },
            },
            "title": "HelmDiffConfig",
            "type": "object",
        },
        "PipelineConfig": {
            "additionalProperties": False,
            "description": "Pipeline configuration unrelated to the components.",
            "properties": {
                "broker": {
                    "description": "The Kafka broker address.",
                    "env": "KPOPS_KAFKA_BROKER",
                    "env_names": ["kpops_kafka_broker"],
                    "title": "Broker",
                    "type": "string",
                },
                "create_namespace": {
                    "default": False,
                    "description": "Flag for `helm upgrade --install`. Create the release namespace if not present.",
                    "env_names": ["create_namespace"],
                    "title": "Create Namespace",
                    "type": "boolean",
                },
                "defaults_filename_prefix": {
                    "default": "defaults",
                    "description": "The name of the defaults file and the prefix of the defaults environment file.",
                    "env_names": ["defaults_filename_prefix"],
                    "title": "Defaults Filename Prefix",
                    "type": "string",
                },
                "defaults_path": {
                    "default": ".",
                    "description": """The path to the folder containing the defaults.yaml file and the environment defaults files. Paths can either be absolute or relative to `config.yaml`""",
                    "env_names": ["defaults_path"],
                    "example": "defaults",
                    "format": "path",
                    "title": "Defaults Path",
                    "type": "string",
                },
                "environment": {
                    "description": "The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).",
                    "env": "KPOPS_ENVIRONMENT",
                    "env_names": ["kpops_environment"],
                    "example": "development",
                    "title": "Environment",
                    "type": "string",
                },
                "helm_config": {
                    "allOf": [{"$ref": "#/definitions/HelmConfig"}],
                    "default": {"context": None, "debug": False},
                    "description": "Global flags for Helm.",
                    "env_names": ["helm_config"],
                    "title": "Helm Config",
                },
                "helm_diff_config": {
                    "allOf": [{"$ref": "#/definitions/HelmDiffConfig"}],
                    "default": {"enable": True, "ignore": []},
                    "description": "Configure Helm Diff.",
                    "env_names": ["helm_diff_config"],
                    "title": "Helm Diff Config",
                },
                "kafka_connect_host": {
                    "description": "Address of Kafka Connect.",
                    "env": "KPOPS_CONNECT_HOST",
                    "env_names": ["kpops_connect_host"],
                    "example": "http://localhost:8083",
                    "title": "Kafka Connect Host",
                    "type": "string",
                },
                "kafka_rest_host": {
                    "description": "Address of the Kafka REST Proxy.",
                    "env": "KPOPS_REST_PROXY_HOST",
                    "env_names": ["kpops_rest_proxy_host"],
                    "example": "http://localhost:8082",
                    "title": "Kafka Rest Host",
                    "type": "string",
                },
                "retain_clean_jobs": {
                    "default": False,
                    "description": "Whether to retain clean up jobs in the cluster or uninstall the, after completion.",
                    "env": "KPOPS_RETAIN_CLEAN_JOBS",
                    "env_names": ["kpops_retain_clean_jobs"],
                    "title": "Retain Clean Jobs",
                    "type": "boolean",
                },
                "schema_registry_url": {
                    "description": "Address of the Schema Registry.",
                    "env": "KPOPS_SCHEMA_REGISTRY_URL",
                    "env_names": ["kpops_schema_registry_url"],
                    "example": "http://localhost:8081",
                    "title": "Schema Registry Url",
                    "type": "string",
                },
                "timeout": {
                    "default": 300,
                    "description": "The timeout in seconds that specifies when actions like deletion or deploy timeout.",
                    "env": "KPOPS_TIMEOUT",
                    "env_names": ["kpops_timeout"],
                    "title": "Timeout",
                    "type": "integer",
                },
                "topic_name_config": {
                    "allOf": [{"$ref": "#/definitions/TopicNameConfig"}],
                    "default": {
                        "default_error_topic_name": "${pipeline_name}-${component_name}-error",
                        "default_output_topic_name": "${pipeline_name}-${component_name}",
                    },
                    "description": "Configure the topic name variables you can use in the pipeline definition.",
                    "env_names": ["topic_name_config"],
                    "title": "Topic Name Config",
                },
            },
            "required": ["environment", "broker"],
            "title": "PipelineConfig",
            "type": "object",
        },
        "TopicNameConfig": {
            "additionalProperties": False,
            "description": "Configures topic names.",
            "properties": {
                "default_error_topic_name": {
                    "default": "${pipeline_name}-${component_name}-error",
                    "description": "Configures the value for the variable ${error_topic_name}",
                    "env_names": ["default_error_topic_name"],
                    "title": "Default Error Topic Name",
                    "type": "string",
                },
                "default_output_topic_name": {
                    "default": "${pipeline_name}-${component_name}",
                    "description": "Configures the value for the variable ${output_topic_name}",
                    "env_names": ["default_output_topic_name"],
                    "title": "Default Output Topic Name",
                    "type": "string",
                },
            },
            "title": "TopicNameConfig",
            "type": "object",
        },
    },
    "title": "kpops config schema",
}

snapshots[
    "TestGenSchema.test_gen_pipeline_schema_with_custom_module test-schema-generation"
] = {
    "definitions": {
        "FromSection": {
            "additionalProperties": False,
            "properties": {
                "topics": {
                    "additionalProperties": {"$ref": "#/definitions/FromTopic"},
                    "title": "Topics",
                    "type": "object",
                }
            },
            "required": ["topics"],
            "title": "FromSection",
            "type": "object",
        },
        "FromTopic": {
            "additionalProperties": False,
            "properties": {
                "role": {"title": "Role", "type": "string"},
                "type": {"$ref": "#/definitions/InputTopicTypes"},
            },
            "required": ["type"],
            "title": "FromTopic",
            "type": "object",
        },
        "HelmRepoConfig": {
            "properties": {
                "repoAuthFlags": {
                    "allOf": [{"$ref": "#/definitions/RepoAuthFlags"}],
                    "default": {
                        "ca_file": None,
                        "insecure_skip_tls_verify": False,
                        "password": None,
                        "username": None,
                    },
                    "title": "Repoauthflags",
                },
                "repositoryName": {"title": "Repositoryname", "type": "string"},
                "url": {"title": "Url", "type": "string"},
            },
            "required": ["repositoryName", "url"],
            "title": "HelmRepoConfig",
            "type": "object",
        },
        "InputTopicTypes": {
            "description": "An enumeration.",
            "enum": ["input", "extra", "input-pattern", "extra-pattern"],
            "title": "InputTopicTypes",
            "type": "string",
        },
        "KafkaApp": {
            "description": """Base component for Kafka-based components.
Producer or streaming apps should inherit from this class.""",
            "properties": {
                "app": {"$ref": "#/definitions/KafkaAppConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                    },
                    "title": "Repoconfig",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-app",
                    "enum": ["kafka-app"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "2.9.0", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaApp",
            "type": "object",
        },
        "KafkaAppConfig": {
            "properties": {
                "nameOverride": {"title": "Nameoverride", "type": "string"},
                "streams": {"$ref": "#/definitions/KafkaStreamsConfig"},
            },
            "required": ["streams"],
            "title": "KafkaAppConfig",
            "type": "object",
        },
        "KafkaConnectConfig": {
            "additionalProperties": {"type": "string"},
            "properties": {},
            "title": "KafkaConnectConfig",
            "type": "object",
        },
        "KafkaConnector": {
            "properties": {
                "app": {"$ref": "#/definitions/KafkaConnectConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                    },
                    "title": "Repoconfig",
                },
                "resetterValues": {
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "title": "Resettervalues",
                    "type": "object",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-connector",
                    "enum": ["kafka-connector"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "1.0.4", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaConnector",
            "type": "object",
        },
        "KafkaSinkConnector": {
            "properties": {
                "app": {"$ref": "#/definitions/KafkaConnectConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                    },
                    "title": "Repoconfig",
                },
                "resetterValues": {
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "title": "Resettervalues",
                    "type": "object",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-sink-connector",
                    "enum": ["kafka-sink-connector"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "1.0.4", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaSinkConnector",
            "type": "object",
        },
        "KafkaSourceConnector": {
            "properties": {
                "app": {"$ref": "#/definitions/KafkaConnectConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "offsetTopic": {"title": "Offsettopic", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                    },
                    "title": "Repoconfig",
                },
                "resetterValues": {
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "title": "Resettervalues",
                    "type": "object",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-source-connector",
                    "enum": ["kafka-source-connector"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "1.0.4", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaSourceConnector",
            "type": "object",
        },
        "KafkaStreamsConfig": {
            "properties": {
                "brokers": {"title": "Brokers", "type": "string"},
                "schemaRegistryUrl": {"title": "Schemaregistryurl", "type": "string"},
            },
            "required": ["brokers"],
            "title": "KafkaStreamsConfig",
            "type": "object",
        },
        "KubernetesApp": {
            "description": "Base Kubernetes app",
            "properties": {
                "app": {"$ref": "#/definitions/KubernetesAppConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {"$ref": "#/definitions/HelmRepoConfig"},
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kubernetes-app",
                    "enum": ["kubernetes-app"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KubernetesApp",
            "type": "object",
        },
        "KubernetesAppConfig": {
            "properties": {},
            "title": "KubernetesAppConfig",
            "type": "object",
        },
        "OutputTopicTypes": {
            "description": """Types of output topic.
    error (error topic), output (output topic), and extra topics. Every extra topic must have a role.
    """,
            "enum": ["error", "output", "extra"],
            "title": "OutputTopicTypes",
            "type": "string",
        },
        "ProducerApp": {
            "description": """Producer component

This producer holds configuration to use as values for the streams bootstrap produce helm chart.""",
            "properties": {
                "app": {"$ref": "#/definitions/ProducerValues"},
                "from": {
                    "description": "Producer doesn't support FromSection",
                    "title": "From",
                    "type": "null",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                    },
                    "title": "Repoconfig",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "producer",
                    "enum": ["producer"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "2.9.0", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "ProducerApp",
            "type": "object",
        },
        "ProducerStreamsConfig": {
            "properties": {
                "brokers": {"title": "Brokers", "type": "string"},
                "extraOutputTopics": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Extraoutputtopics",
                    "type": "object",
                },
                "outputTopic": {"title": "Outputtopic", "type": "string"},
                "schemaRegistryUrl": {"title": "Schemaregistryurl", "type": "string"},
            },
            "required": ["brokers"],
            "title": "ProducerStreamsConfig",
            "type": "object",
        },
        "ProducerValues": {
            "properties": {
                "nameOverride": {"title": "Nameoverride", "type": "string"},
                "streams": {"$ref": "#/definitions/ProducerStreamsConfig"},
            },
            "required": ["streams"],
            "title": "ProducerValues",
            "type": "object",
        },
        "RepoAuthFlags": {
            "properties": {
                "caFile": {"format": "path", "title": "Cafile", "type": "string"},
                "insecureSkipTlsVerify": {
                    "default": False,
                    "title": "Insecureskiptlsverify",
                    "type": "boolean",
                },
                "password": {"title": "Password", "type": "string"},
                "username": {"title": "Username", "type": "string"},
            },
            "title": "RepoAuthFlags",
            "type": "object",
        },
        "StreamsApp": {
            "description": "StreamsApp component that configures a streams bootstrap app",
            "properties": {
                "app": {"$ref": "#/definitions/StreamsAppConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                    },
                    "title": "Repoconfig",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "streams-app",
                    "enum": ["streams-app"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "2.9.0", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "StreamsApp",
            "type": "object",
        },
        "StreamsAppAutoScaling": {
            "properties": {
                "consumerGroup": {
                    "description": "Name of the consumer group used for checking the offset on the topic and processing the related lag.",
                    "title": "Consumer group",
                    "type": "string",
                },
                "cooldownPeriod": {
                    "default": 300,
                    "description": "The period to wait after the last trigger reported active before scaling the resource back to 0. https://keda.sh/docs/2.9/concepts/scaling-deployments/#cooldownperiod",
                    "title": "Cooldown period",
                    "type": "integer",
                },
                "enabled": {
                    "default": False,
                    "description": "Whether to enable auto-scaling using KEDA.",
                    "title": "Enabled",
                    "type": "boolean",
                },
                "idleReplicas": {
                    "description": "If this property is set, KEDA will scale the resource down to this number of replicas. https://keda.sh/docs/2.9/concepts/scaling-deployments/#idlereplicacount",
                    "title": "Idle replica count",
                    "type": "integer",
                },
                "lagThreshold": {
                    "description": "Average target value to trigger scaling actions.",
                    "title": "Lag threshold",
                    "type": "integer",
                },
                "maxReplicas": {
                    "default": 1,
                    "description": "This setting is passed to the HPA definition that KEDA will create for a given resource and holds the maximum number of replicas of the target resouce. https://keda.sh/docs/2.9/concepts/scaling-deployments/#maxreplicacount",
                    "title": "Max replica count",
                    "type": "integer",
                },
                "minReplicas": {
                    "default": 0,
                    "description": "Minimum number of replicas KEDA will scale the resource down to. https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount",
                    "title": "Min replica count",
                    "type": "integer",
                },
                "offsetResetPolicy": {
                    "default": "earliest",
                    "description": "The offset reset policy for the consumer if the the consumer group is not yet subscribed to a partition.",
                    "title": "Offset reset policy",
                    "type": "string",
                },
                "pollingInterval": {
                    "default": 30,
                    "description": "This is the interval to check each trigger on. https://keda.sh/docs/2.9/concepts/scaling-deployments/#pollinginterval",
                    "title": "Polling interval",
                    "type": "integer",
                },
                "topics": {
                    "default": [],
                    "description": "List of auto-generated Kafka Streams topics used by the streams app.",
                    "items": {"type": "string"},
                    "title": "Topics",
                    "type": "array",
                },
            },
            "required": ["consumerGroup", "lagThreshold"],
            "title": "StreamsAppAutoScaling",
            "type": "object",
        },
        "StreamsAppConfig": {
            "description": """StreamsBoostrap app configurations.

The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.""",
            "properties": {
                "autoscaling": {"$ref": "#/definitions/StreamsAppAutoScaling"},
                "nameOverride": {"title": "Nameoverride", "type": "string"},
                "streams": {"$ref": "#/definitions/StreamsConfig"},
            },
            "required": ["streams"],
            "title": "StreamsAppConfig",
            "type": "object",
        },
        "StreamsConfig": {
            "description": "Streams Bootstrap streams section",
            "properties": {
                "brokers": {"title": "Brokers", "type": "string"},
                "config": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Config",
                    "type": "object",
                },
                "errorTopic": {"title": "Errortopic", "type": "string"},
                "extraInputPatterns": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Extrainputpatterns",
                    "type": "object",
                },
                "extraInputTopics": {
                    "additionalProperties": {
                        "items": {"type": "string"},
                        "type": "array",
                    },
                    "default": {},
                    "title": "Extrainputtopics",
                    "type": "object",
                },
                "extraOutputTopics": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Extraoutputtopics",
                    "type": "object",
                },
                "inputPattern": {"title": "Inputpattern", "type": "string"},
                "inputTopics": {
                    "default": [],
                    "items": {"type": "string"},
                    "title": "Inputtopics",
                    "type": "array",
                },
                "outputTopic": {"title": "Outputtopic", "type": "string"},
                "schemaRegistryUrl": {"title": "Schemaregistryurl", "type": "string"},
            },
            "required": ["brokers"],
            "title": "StreamsConfig",
            "type": "object",
        },
        "SubComponent": {
            "properties": {
                "app": {"title": "App"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "sub-component",
                    "enum": ["sub-component"],
                    "title": "Schema Type",
                    "type": "string",
                },
            },
            "required": ["name"],
            "title": "SubComponent",
            "type": "object",
        },
        "SubSubComponent": {
            "properties": {
                "app": {"title": "App"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "sub-sub-component",
                    "enum": ["sub-sub-component"],
                    "title": "Schema Type",
                    "type": "string",
                },
            },
            "required": ["name"],
            "title": "SubSubComponent",
            "type": "object",
        },
        "ToSection": {
            "properties": {
                "models": {"default": {}, "title": "Models", "type": "object"},
                "topics": {
                    "additionalProperties": {"$ref": "#/definitions/TopicConfig"},
                    "title": "Topics",
                    "type": "object",
                },
            },
            "required": ["topics"],
            "title": "ToSection",
            "type": "object",
        },
        "TopicConfig": {
            "additionalProperties": False,
            "description": "Configures a topic",
            "properties": {
                "configs": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Configs",
                    "type": "object",
                },
                "keySchema": {"title": "Keyschema", "type": "string"},
                "partitions_count": {"title": "Partitions Count", "type": "integer"},
                "replication_factor": {
                    "title": "Replication Factor",
                    "type": "integer",
                },
                "role": {"title": "Role", "type": "string"},
                "type": {"$ref": "#/definitions/OutputTopicTypes"},
                "valueSchema": {"title": "Valueschema", "type": "string"},
            },
            "required": ["type"],
            "title": "TopicConfig",
            "type": "object",
        },
    },
    "items": {
        "discriminator": {
            "mapping": {
                "kafka-app": "#/definitions/KafkaApp",
                "kafka-connector": "#/definitions/KafkaConnector",
                "kafka-sink-connector": "#/definitions/KafkaSinkConnector",
                "kafka-source-connector": "#/definitions/KafkaSourceConnector",
                "kubernetes-app": "#/definitions/KubernetesApp",
                "producer": "#/definitions/ProducerApp",
                "streams-app": "#/definitions/StreamsApp",
                "sub-component": "#/definitions/SubComponent",
                "sub-sub-component": "#/definitions/SubSubComponent",
            },
            "propertyName": "type",
        },
        "oneOf": [
            {"$ref": "#/definitions/KafkaConnector"},
            {"$ref": "#/definitions/KafkaApp"},
            {"$ref": "#/definitions/KafkaSinkConnector"},
            {"$ref": "#/definitions/KafkaSourceConnector"},
            {"$ref": "#/definitions/KubernetesApp"},
            {"$ref": "#/definitions/ProducerApp"},
            {"$ref": "#/definitions/StreamsApp"},
            {"$ref": "#/definitions/SubComponent"},
            {"$ref": "#/definitions/SubSubComponent"},
        ],
    },
    "title": "kpops pipeline schema",
    "type": "array",
}

snapshots[
    "TestGenSchema.test_gen_pipeline_schema_without_custom_module test-schema-generation"
] = {
    "definitions": {
        "FromSection": {
            "additionalProperties": False,
            "properties": {
                "topics": {
                    "additionalProperties": {"$ref": "#/definitions/FromTopic"},
                    "title": "Topics",
                    "type": "object",
                }
            },
            "required": ["topics"],
            "title": "FromSection",
            "type": "object",
        },
        "FromTopic": {
            "additionalProperties": False,
            "properties": {
                "role": {"title": "Role", "type": "string"},
                "type": {"$ref": "#/definitions/InputTopicTypes"},
            },
            "required": ["type"],
            "title": "FromTopic",
            "type": "object",
        },
        "HelmRepoConfig": {
            "properties": {
                "repoAuthFlags": {
                    "allOf": [{"$ref": "#/definitions/RepoAuthFlags"}],
                    "default": {
                        "ca_file": None,
                        "insecure_skip_tls_verify": False,
                        "password": None,
                        "username": None,
                    },
                    "title": "Repoauthflags",
                },
                "repositoryName": {"title": "Repositoryname", "type": "string"},
                "url": {"title": "Url", "type": "string"},
            },
            "required": ["repositoryName", "url"],
            "title": "HelmRepoConfig",
            "type": "object",
        },
        "InputTopicTypes": {
            "description": "An enumeration.",
            "enum": ["input", "extra", "input-pattern", "extra-pattern"],
            "title": "InputTopicTypes",
            "type": "string",
        },
        "KafkaApp": {
            "description": """Base component for Kafka-based components.
Producer or streaming apps should inherit from this class.""",
            "properties": {
                "app": {"$ref": "#/definitions/KafkaAppConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                    },
                    "title": "Repoconfig",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-app",
                    "enum": ["kafka-app"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "2.9.0", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaApp",
            "type": "object",
        },
        "KafkaAppConfig": {
            "properties": {
                "nameOverride": {"title": "Nameoverride", "type": "string"},
                "streams": {"$ref": "#/definitions/KafkaStreamsConfig"},
            },
            "required": ["streams"],
            "title": "KafkaAppConfig",
            "type": "object",
        },
        "KafkaConnectConfig": {
            "additionalProperties": {"type": "string"},
            "properties": {},
            "title": "KafkaConnectConfig",
            "type": "object",
        },
        "KafkaConnector": {
            "properties": {
                "app": {"$ref": "#/definitions/KafkaConnectConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                    },
                    "title": "Repoconfig",
                },
                "resetterValues": {
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "title": "Resettervalues",
                    "type": "object",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-connector",
                    "enum": ["kafka-connector"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "1.0.4", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaConnector",
            "type": "object",
        },
        "KafkaSinkConnector": {
            "properties": {
                "app": {"$ref": "#/definitions/KafkaConnectConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                    },
                    "title": "Repoconfig",
                },
                "resetterValues": {
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "title": "Resettervalues",
                    "type": "object",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-sink-connector",
                    "enum": ["kafka-sink-connector"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "1.0.4", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaSinkConnector",
            "type": "object",
        },
        "KafkaSourceConnector": {
            "properties": {
                "app": {"$ref": "#/definitions/KafkaConnectConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "offsetTopic": {"title": "Offsettopic", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                    },
                    "title": "Repoconfig",
                },
                "resetterValues": {
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "title": "Resettervalues",
                    "type": "object",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kafka-source-connector",
                    "enum": ["kafka-source-connector"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "1.0.4", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KafkaSourceConnector",
            "type": "object",
        },
        "KafkaStreamsConfig": {
            "properties": {
                "brokers": {"title": "Brokers", "type": "string"},
                "schemaRegistryUrl": {"title": "Schemaregistryurl", "type": "string"},
            },
            "required": ["brokers"],
            "title": "KafkaStreamsConfig",
            "type": "object",
        },
        "KubernetesApp": {
            "description": "Base Kubernetes app",
            "properties": {
                "app": {"$ref": "#/definitions/KubernetesAppConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {"$ref": "#/definitions/HelmRepoConfig"},
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "kubernetes-app",
                    "enum": ["kubernetes-app"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "KubernetesApp",
            "type": "object",
        },
        "KubernetesAppConfig": {
            "properties": {},
            "title": "KubernetesAppConfig",
            "type": "object",
        },
        "OutputTopicTypes": {
            "description": """Types of output topic.
    error (error topic), output (output topic), and extra topics. Every extra topic must have a role.
    """,
            "enum": ["error", "output", "extra"],
            "title": "OutputTopicTypes",
            "type": "string",
        },
        "ProducerApp": {
            "description": """Producer component

This producer holds configuration to use as values for the streams bootstrap produce helm chart.""",
            "properties": {
                "app": {"$ref": "#/definitions/ProducerValues"},
                "from": {
                    "description": "Producer doesn't support FromSection",
                    "title": "From",
                    "type": "null",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                    },
                    "title": "Repoconfig",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "producer",
                    "enum": ["producer"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "2.9.0", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "ProducerApp",
            "type": "object",
        },
        "ProducerStreamsConfig": {
            "properties": {
                "brokers": {"title": "Brokers", "type": "string"},
                "extraOutputTopics": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Extraoutputtopics",
                    "type": "object",
                },
                "outputTopic": {"title": "Outputtopic", "type": "string"},
                "schemaRegistryUrl": {"title": "Schemaregistryurl", "type": "string"},
            },
            "required": ["brokers"],
            "title": "ProducerStreamsConfig",
            "type": "object",
        },
        "ProducerValues": {
            "properties": {
                "nameOverride": {"title": "Nameoverride", "type": "string"},
                "streams": {"$ref": "#/definitions/ProducerStreamsConfig"},
            },
            "required": ["streams"],
            "title": "ProducerValues",
            "type": "object",
        },
        "RepoAuthFlags": {
            "properties": {
                "caFile": {"format": "path", "title": "Cafile", "type": "string"},
                "insecureSkipTlsVerify": {
                    "default": False,
                    "title": "Insecureskiptlsverify",
                    "type": "boolean",
                },
                "password": {"title": "Password", "type": "string"},
                "username": {"title": "Username", "type": "string"},
            },
            "title": "RepoAuthFlags",
            "type": "object",
        },
        "StreamsApp": {
            "description": "StreamsApp component that configures a streams bootstrap app",
            "properties": {
                "app": {"$ref": "#/definitions/StreamsAppConfig"},
                "from": {
                    "allOf": [{"$ref": "#/definitions/FromSection"}],
                    "title": "From",
                },
                "name": {"title": "Name", "type": "string"},
                "namespace": {"title": "Namespace", "type": "string"},
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string",
                },
                "repoConfig": {
                    "allOf": [{"$ref": "#/definitions/HelmRepoConfig"}],
                    "default": {
                        "repo_auth_flags": {
                            "ca_file": None,
                            "insecure_skip_tls_verify": False,
                            "password": None,
                            "username": None,
                        },
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                    },
                    "title": "Repoconfig",
                },
                "to": {"$ref": "#/definitions/ToSection"},
                "type": {
                    "default": "streams-app",
                    "enum": ["streams-app"],
                    "title": "Schema Type",
                    "type": "string",
                },
                "version": {"default": "2.9.0", "title": "Version", "type": "string"},
            },
            "required": ["name", "app", "namespace"],
            "title": "StreamsApp",
            "type": "object",
        },
        "StreamsAppAutoScaling": {
            "properties": {
                "consumerGroup": {
                    "description": "Name of the consumer group used for checking the offset on the topic and processing the related lag.",
                    "title": "Consumer group",
                    "type": "string",
                },
                "cooldownPeriod": {
                    "default": 300,
                    "description": "The period to wait after the last trigger reported active before scaling the resource back to 0. https://keda.sh/docs/2.9/concepts/scaling-deployments/#cooldownperiod",
                    "title": "Cooldown period",
                    "type": "integer",
                },
                "enabled": {
                    "default": False,
                    "description": "Whether to enable auto-scaling using KEDA.",
                    "title": "Enabled",
                    "type": "boolean",
                },
                "idleReplicas": {
                    "description": "If this property is set, KEDA will scale the resource down to this number of replicas. https://keda.sh/docs/2.9/concepts/scaling-deployments/#idlereplicacount",
                    "title": "Idle replica count",
                    "type": "integer",
                },
                "lagThreshold": {
                    "description": "Average target value to trigger scaling actions.",
                    "title": "Lag threshold",
                    "type": "integer",
                },
                "maxReplicas": {
                    "default": 1,
                    "description": "This setting is passed to the HPA definition that KEDA will create for a given resource and holds the maximum number of replicas of the target resouce. https://keda.sh/docs/2.9/concepts/scaling-deployments/#maxreplicacount",
                    "title": "Max replica count",
                    "type": "integer",
                },
                "minReplicas": {
                    "default": 0,
                    "description": "Minimum number of replicas KEDA will scale the resource down to. https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount",
                    "title": "Min replica count",
                    "type": "integer",
                },
                "offsetResetPolicy": {
                    "default": "earliest",
                    "description": "The offset reset policy for the consumer if the the consumer group is not yet subscribed to a partition.",
                    "title": "Offset reset policy",
                    "type": "string",
                },
                "pollingInterval": {
                    "default": 30,
                    "description": "This is the interval to check each trigger on. https://keda.sh/docs/2.9/concepts/scaling-deployments/#pollinginterval",
                    "title": "Polling interval",
                    "type": "integer",
                },
                "topics": {
                    "default": [],
                    "description": "List of auto-generated Kafka Streams topics used by the streams app.",
                    "items": {"type": "string"},
                    "title": "Topics",
                    "type": "array",
                },
            },
            "required": ["consumerGroup", "lagThreshold"],
            "title": "StreamsAppAutoScaling",
            "type": "object",
        },
        "StreamsAppConfig": {
            "description": """StreamsBoostrap app configurations.

The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.""",
            "properties": {
                "autoscaling": {"$ref": "#/definitions/StreamsAppAutoScaling"},
                "nameOverride": {"title": "Nameoverride", "type": "string"},
                "streams": {"$ref": "#/definitions/StreamsConfig"},
            },
            "required": ["streams"],
            "title": "StreamsAppConfig",
            "type": "object",
        },
        "StreamsConfig": {
            "description": "Streams Bootstrap streams section",
            "properties": {
                "brokers": {"title": "Brokers", "type": "string"},
                "config": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Config",
                    "type": "object",
                },
                "errorTopic": {"title": "Errortopic", "type": "string"},
                "extraInputPatterns": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Extrainputpatterns",
                    "type": "object",
                },
                "extraInputTopics": {
                    "additionalProperties": {
                        "items": {"type": "string"},
                        "type": "array",
                    },
                    "default": {},
                    "title": "Extrainputtopics",
                    "type": "object",
                },
                "extraOutputTopics": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Extraoutputtopics",
                    "type": "object",
                },
                "inputPattern": {"title": "Inputpattern", "type": "string"},
                "inputTopics": {
                    "default": [],
                    "items": {"type": "string"},
                    "title": "Inputtopics",
                    "type": "array",
                },
                "outputTopic": {"title": "Outputtopic", "type": "string"},
                "schemaRegistryUrl": {"title": "Schemaregistryurl", "type": "string"},
            },
            "required": ["brokers"],
            "title": "StreamsConfig",
            "type": "object",
        },
        "ToSection": {
            "properties": {
                "models": {"default": {}, "title": "Models", "type": "object"},
                "topics": {
                    "additionalProperties": {"$ref": "#/definitions/TopicConfig"},
                    "title": "Topics",
                    "type": "object",
                },
            },
            "required": ["topics"],
            "title": "ToSection",
            "type": "object",
        },
        "TopicConfig": {
            "additionalProperties": False,
            "description": "Configures a topic",
            "properties": {
                "configs": {
                    "additionalProperties": {"type": "string"},
                    "default": {},
                    "title": "Configs",
                    "type": "object",
                },
                "keySchema": {"title": "Keyschema", "type": "string"},
                "partitions_count": {"title": "Partitions Count", "type": "integer"},
                "replication_factor": {
                    "title": "Replication Factor",
                    "type": "integer",
                },
                "role": {"title": "Role", "type": "string"},
                "type": {"$ref": "#/definitions/OutputTopicTypes"},
                "valueSchema": {"title": "Valueschema", "type": "string"},
            },
            "required": ["type"],
            "title": "TopicConfig",
            "type": "object",
        },
    },
    "items": {
        "discriminator": {
            "mapping": {
                "kafka-app": "#/definitions/KafkaApp",
                "kafka-connector": "#/definitions/KafkaConnector",
                "kafka-sink-connector": "#/definitions/KafkaSinkConnector",
                "kafka-source-connector": "#/definitions/KafkaSourceConnector",
                "kubernetes-app": "#/definitions/KubernetesApp",
                "producer": "#/definitions/ProducerApp",
                "streams-app": "#/definitions/StreamsApp",
            },
            "propertyName": "type",
        },
        "oneOf": [
            {"$ref": "#/definitions/KafkaConnector"},
            {"$ref": "#/definitions/KafkaApp"},
            {"$ref": "#/definitions/KafkaSinkConnector"},
            {"$ref": "#/definitions/KafkaSourceConnector"},
            {"$ref": "#/definitions/KubernetesApp"},
            {"$ref": "#/definitions/ProducerApp"},
            {"$ref": "#/definitions/StreamsApp"},
        ],
    },
    "title": "kpops pipeline schema",
    "type": "array",
}
