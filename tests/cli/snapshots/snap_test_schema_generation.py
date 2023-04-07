# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots[
    "TestGenSchema.test_gen_config_schema test-schema-generation"
] = """{
    "title": "kpops config schema",
    "$ref": "#/definitions/PipelineConfig",
    "definitions": {
        "TopicNameConfig": {
            "title": "TopicNameConfig",
            "description": "Configures topic names.",
            "type": "object",
            "properties": {
                "default_output_topic_name": {
                    "title": "Default Output Topic Name",
                    "description": "Configures the value for the variable ${output_topic_name}",
                    "default": "${pipeline_name}-${component_name}",
                    "env_names": [
                        "default_output_topic_name"
                    ],
                    "type": "string"
                },
                "default_error_topic_name": {
                    "title": "Default Error Topic Name",
                    "description": "Configures the value for the variable ${error_topic_name}",
                    "default": "${pipeline_name}-${component_name}-error",
                    "env_names": [
                        "default_error_topic_name"
                    ],
                    "type": "string"
                }
            },
            "additionalProperties": false
        },
        "HelmConfig": {
            "title": "HelmConfig",
            "type": "object",
            "properties": {
                "context": {
                    "title": "Context",
                    "description": "Set the name of the kubeconfig context. (--kube-context)",
                    "example": "dev-storage",
                    "type": "string"
                },
                "debug": {
                    "title": "Debug",
                    "description": "Run Helm in Debug mode.",
                    "default": false,
                    "type": "boolean"
                }
            }
        },
        "HelmDiffConfig": {
            "title": "HelmDiffConfig",
            "type": "object",
            "properties": {
                "enable": {
                    "title": "Enable",
                    "description": "Enable Helm Diff.",
                    "default": true,
                    "type": "boolean"
                },
                "ignore": {
                    "title": "Ignore",
                    "description": "Set of keys that should not be checked.",
                    "example": "- name\\n- imageTag",
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "uniqueItems": true
                }
            }
        },
        "PipelineConfig": {
            "title": "PipelineConfig",
            "description": "Pipeline configuration unrelated to the components.",
            "type": "object",
            "properties": {
                "defaults_path": {
                    "title": "Defaults Path",
                    "description": "The path to the folder containing the defaults.yaml file and the environment defaults files. Paths can either be absolute or relative to `config.yaml`",
                    "default": ".",
                    "example": "defaults",
                    "env_names": [
                        "defaults_path"
                    ],
                    "type": "string",
                    "format": "path"
                },
                "environment": {
                    "title": "Environment",
                    "description": "The environment you want to generate and deploy the pipeline to. Suffix your environment files with this value (e.g. defaults_development.yaml for environment=development).",
                    "env": "KPOPS_ENVIRONMENT",
                    "example": "development",
                    "env_names": [
                        "kpops_environment"
                    ],
                    "type": "string"
                },
                "broker": {
                    "title": "Broker",
                    "description": "The Kafka broker address.",
                    "env": "KPOPS_KAFKA_BROKER",
                    "env_names": [
                        "kpops_kafka_broker"
                    ],
                    "type": "string"
                },
                "defaults_filename_prefix": {
                    "title": "Defaults Filename Prefix",
                    "description": "The name of the defaults file and the prefix of the defaults environment file.",
                    "default": "defaults",
                    "env_names": [
                        "defaults_filename_prefix"
                    ],
                    "type": "string"
                },
                "topic_name_config": {
                    "title": "Topic Name Config",
                    "description": "Configure the topic name variables you can use in the pipeline definition.",
                    "default": {
                        "default_output_topic_name": "${pipeline_name}-${component_name}",
                        "default_error_topic_name": "${pipeline_name}-${component_name}-error"
                    },
                    "env_names": [
                        "topic_name_config"
                    ],
                    "allOf": [
                        {
                            "$ref": "#/definitions/TopicNameConfig"
                        }
                    ]
                },
                "schema_registry_url": {
                    "title": "Schema Registry Url",
                    "description": "Address of the Schema Registry.",
                    "example": "http://localhost:8081",
                    "env": "KPOPS_SCHEMA_REGISTRY_URL",
                    "env_names": [
                        "kpops_schema_registry_url"
                    ],
                    "type": "string"
                },
                "kafka_rest_host": {
                    "title": "Kafka Rest Host",
                    "description": "Address of the Kafka REST Proxy.",
                    "env": "KPOPS_REST_PROXY_HOST",
                    "example": "http://localhost:8082",
                    "env_names": [
                        "kpops_rest_proxy_host"
                    ],
                    "type": "string"
                },
                "kafka_connect_host": {
                    "title": "Kafka Connect Host",
                    "description": "Address of Kafka Connect.",
                    "env": "KPOPS_CONNECT_HOST",
                    "example": "http://localhost:8083",
                    "env_names": [
                        "kpops_connect_host"
                    ],
                    "type": "string"
                },
                "timeout": {
                    "title": "Timeout",
                    "description": "The timeout in seconds that specifies when actions like deletion or deploy timeout.",
                    "default": 300,
                    "env": "KPOPS_TIMEOUT",
                    "env_names": [
                        "kpops_timeout"
                    ],
                    "type": "integer"
                },
                "create_namespace": {
                    "title": "Create Namespace",
                    "description": "Flag for `helm upgrade --install`. Create the release namespace if not present.",
                    "default": false,
                    "env_names": [
                        "create_namespace"
                    ],
                    "type": "boolean"
                },
                "helm_config": {
                    "title": "Helm Config",
                    "description": "Global flags for Helm.",
                    "default": {
                        "context": null,
                        "debug": false
                    },
                    "env_names": [
                        "helm_config"
                    ],
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmConfig"
                        }
                    ]
                },
                "helm_diff_config": {
                    "title": "Helm Diff Config",
                    "description": "Configure Helm Diff.",
                    "default": {
                        "enable": true,
                        "ignore": []
                    },
                    "env_names": [
                        "helm_diff_config"
                    ],
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmDiffConfig"
                        }
                    ]
                },
                "retain_clean_jobs": {
                    "title": "Retain Clean Jobs",
                    "description": "Whether to retain clean up jobs in the cluster or uninstall the, after completion.",
                    "default": false,
                    "env": "KPOPS_RETAIN_CLEAN_JOBS",
                    "env_names": [
                        "kpops_retain_clean_jobs"
                    ],
                    "type": "boolean"
                }
            },
            "required": [
                "environment",
                "broker"
            ],
            "additionalProperties": false
        }
    }
}
"""

snapshots[
    "TestGenSchema.test_gen_pipeline_schema_with_custom_module test-schema-generation"
] = """{
    "title": "kpops pipeline schema",
    "type": "array",
    "items": {
        "discriminator": {
            "propertyName": "type",
            "mapping": {
                "kafka-app": "#/definitions/KafkaApp",
                "kafka-connector": "#/definitions/KafkaConnector",
                "kafka-sink-connector": "#/definitions/KafkaSinkConnector",
                "kafka-source-connector": "#/definitions/KafkaSourceConnector",
                "kubernetes-app": "#/definitions/KubernetesApp",
                "producer": "#/definitions/ProducerApp",
                "streams-app": "#/definitions/StreamsApp",
                "sub-pipeline-component": "#/definitions/SubPipelineComponent",
                "sub-pipeline-component-correct": "#/definitions/SubPipelineComponentCorrect"
            }
        },
        "oneOf": [
            {
                "$ref": "#/definitions/KafkaApp"
            },
            {
                "$ref": "#/definitions/KafkaConnector"
            },
            {
                "$ref": "#/definitions/KafkaSinkConnector"
            },
            {
                "$ref": "#/definitions/KafkaSourceConnector"
            },
            {
                "$ref": "#/definitions/KubernetesApp"
            },
            {
                "$ref": "#/definitions/ProducerApp"
            },
            {
                "$ref": "#/definitions/StreamsApp"
            },
            {
                "$ref": "#/definitions/SubPipelineComponent"
            },
            {
                "$ref": "#/definitions/SubPipelineComponentCorrect"
            }
        ]
    },
    "definitions": {
        "InputTopicTypes": {
            "title": "InputTopicTypes",
            "description": "Input topic types\\n\\n    input (input topic), input_pattern (input pattern topic), extra (extra topic), extra_pattern (extra pattern topic).\\n    Every extra topic must have a role.\\n    ",
            "enum": [
                "input",
                "extra",
                "input-pattern",
                "extra-pattern"
            ],
            "type": "string"
        },
        "FromTopic": {
            "title": "FromTopic",
            "description": "Input topic\\n\\n:param type: Topic type\\n:type type: InputTopicTypes\\n:param role: Custom identifier belonging to a topic, provide only if `type` is `extra` or `extra-pattern`\\n:type role: str | None",
            "type": "object",
            "properties": {
                "type": {
                    "description": "Topic type",
                    "allOf": [
                        {
                            "$ref": "#/definitions/InputTopicTypes"
                        }
                    ]
                },
                "role": {
                    "title": "Role",
                    "description": "Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
                    "type": "string"
                }
            },
            "required": [
                "type"
            ],
            "additionalProperties": false
        },
        "FromSection": {
            "title": "FromSection",
            "description": "Holds multiple input topics\\n\\n:param topics: Input topics\\n:type topics: dict[str, FromTopic]",
            "type": "object",
            "properties": {
                "topics": {
                    "title": "Topics",
                    "description": "Input topics",
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    }
                }
            },
            "required": [
                "topics"
            ],
            "additionalProperties": false
        },
        "KafkaStreamsConfig": {
            "title": "KafkaStreamsConfig",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "KafkaAppConfig": {
            "title": "KafkaAppConfig",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/KafkaStreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "type": "string"
                }
            },
            "required": [
                "streams"
            ]
        },
        "OutputTopicTypes": {
            "title": "OutputTopicTypes",
            "description": "Types of output topic\\n\\n    Error (error topic), output (output topic), and extra topics. Every extra topic must have a role.\\n    ",
            "enum": [
                "error",
                "output",
                "extra"
            ],
            "type": "string"
        },
        "TopicConfig": {
            "title": "TopicConfig",
            "description": "Configure an output topic\\n\\n:param type: Topic type\\n:type type: InputTopicTypes\\n:param key_schema: Key schema class name\\n:type key_schema: str | None\\n:param partitions_count: Number of partitions into which the topic is divided\\n:type partitions_count: int | None\\n:param replication_factor: Replication topic of the topic\\n:type replication_factor: int | None\\n:param configs: Topic configs\\n:type configs: dict[str, str | int]\\n:param role: Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`\\n:type role: str | None",
            "type": "object",
            "properties": {
                "type": {
                    "description": "Topic type",
                    "allOf": [
                        {
                            "$ref": "#/definitions/OutputTopicTypes"
                        }
                    ]
                },
                "keySchema": {
                    "title": "Keyschema",
                    "description": "Key schema class name",
                    "type": "string"
                },
                "valueSchema": {
                    "title": "Valueschema",
                    "description": "Value schema class name",
                    "type": "string"
                },
                "partitions_count": {
                    "title": "Partitions Count",
                    "description": "Number of partitions into which the topic is divided",
                    "type": "integer"
                },
                "replication_factor": {
                    "title": "Replication Factor",
                    "description": "Replication topic of the topic",
                    "type": "integer"
                },
                "configs": {
                    "title": "Configs",
                    "description": "Topic configs",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "anyOf": [
                            {
                                "type": "string"
                            },
                            {
                                "type": "integer"
                            }
                        ]
                    }
                },
                "role": {
                    "title": "Role",
                    "description": "Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
                    "type": "string"
                }
            },
            "required": [
                "type"
            ],
            "additionalProperties": false
        },
        "ToSection": {
            "title": "ToSection",
            "description": "Holds multiple output topics\\n\\n:param models: Data models\\n:type models: dict[str, Any]\\n:param topics: Output topics\\n:type topics: dict[str, TopicConfig]",
            "type": "object",
            "properties": {
                "models": {
                    "title": "Models",
                    "default": {},
                    "type": "object"
                },
                "topics": {
                    "title": "Topics",
                    "description": "Output topics",
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/TopicConfig"
                    }
                }
            },
            "required": [
                "topics"
            ]
        },
        "RepoAuthFlags": {
            "title": "RepoAuthFlags",
            "type": "object",
            "properties": {
                "username": {
                    "title": "Username",
                    "type": "string"
                },
                "password": {
                    "title": "Password",
                    "type": "string"
                },
                "caFile": {
                    "title": "Cafile",
                    "type": "string",
                    "format": "path"
                },
                "insecureSkipTlsVerify": {
                    "title": "Insecureskiptlsverify",
                    "default": false,
                    "type": "boolean"
                }
            }
        },
        "HelmRepoConfig": {
            "title": "HelmRepoConfig",
            "type": "object",
            "properties": {
                "repositoryName": {
                    "title": "Repositoryname",
                    "type": "string"
                },
                "url": {
                    "title": "Url",
                    "type": "string"
                },
                "repoAuthFlags": {
                    "title": "Repoauthflags",
                    "default": {
                        "username": null,
                        "password": null,
                        "ca_file": null,
                        "insecure_skip_tls_verify": false
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/RepoAuthFlags"
                        }
                    ]
                }
            },
            "required": [
                "repositoryName",
                "url"
            ]
        },
        "KafkaApp": {
            "title": "KafkaApp",
            "description": "Base component for Kafka-based components.\\nProducer or streaming apps should inherit from this class.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-app",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaAppConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-app",
                    "enum": [
                        "kafka-app"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "2.9.0",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KafkaConnectConfig": {
            "title": "KafkaConnectConfig",
            "type": "object",
            "properties": {},
            "additionalProperties": {
                "type": "string"
            }
        },
        "KafkaConnector": {
            "title": "KafkaConnector",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-connector",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaConnectConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-connector",
                    "enum": [
                        "kafka-connector"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KafkaSinkConnector": {
            "title": "KafkaSinkConnector",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-sink-connector",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaConnectConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-sink-connector",
                    "enum": [
                        "kafka-sink-connector"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KafkaSourceConnector": {
            "title": "KafkaSourceConnector",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-source-connector",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaConnectConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-source-connector",
                    "enum": [
                        "kafka-source-connector"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "offsetTopic": {
                    "title": "Offsettopic",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KubernetesAppConfig": {
            "title": "KubernetesAppConfig",
            "type": "object",
            "properties": {}
        },
        "KubernetesApp": {
            "title": "KubernetesApp",
            "description": "Base Kubernetes app",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kubernetes-app",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KubernetesAppConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kubernetes-app",
                    "enum": [
                        "kubernetes-app"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "$ref": "#/definitions/HelmRepoConfig"
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "ProducerStreamsConfig": {
            "title": "ProducerStreamsConfig",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "type": "string"
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "ProducerValues": {
            "title": "ProducerValues",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/ProducerStreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "type": "string"
                }
            },
            "required": [
                "streams"
            ]
        },
        "ProducerApp": {
            "title": "ProducerApp",
            "description": "Producer component\\n\\nThis producer holds configuration to use as values for the streams bootstrap produce helm chart.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "producer",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Producer doesn\'t support FromSection",
                    "type": "null"
                },
                "app": {
                    "$ref": "#/definitions/ProducerValues"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "producer",
                    "enum": [
                        "producer"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "2.9.0",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "StreamsConfig": {
            "title": "StreamsConfig",
            "description": "Streams Bootstrap streams section",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "type": "string"
                },
                "inputTopics": {
                    "title": "Inputtopics",
                    "default": [],
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "inputPattern": {
                    "title": "Inputpattern",
                    "type": "string"
                },
                "extraInputTopics": {
                    "title": "Extrainputtopics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "extraInputPatterns": {
                    "title": "Extrainputpatterns",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "type": "string"
                },
                "errorTopic": {
                    "title": "Errortopic",
                    "type": "string"
                },
                "config": {
                    "title": "Config",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "brokers"
            ]
        },
        "StreamsAppAutoScaling": {
            "title": "StreamsAppAutoScaling",
            "type": "object",
            "properties": {
                "enabled": {
                    "title": "Enabled",
                    "description": "Whether to enable auto-scaling using KEDA.",
                    "default": false,
                    "type": "boolean"
                },
                "consumerGroup": {
                    "title": "Consumer group",
                    "description": "Name of the consumer group used for checking the offset on the topic and processing the related lag.",
                    "type": "string"
                },
                "lagThreshold": {
                    "title": "Lag threshold",
                    "description": "Average target value to trigger scaling actions.",
                    "type": "integer"
                },
                "pollingInterval": {
                    "title": "Polling interval",
                    "description": "This is the interval to check each trigger on. https://keda.sh/docs/2.9/concepts/scaling-deployments/#pollinginterval",
                    "default": 30,
                    "type": "integer"
                },
                "cooldownPeriod": {
                    "title": "Cooldown period",
                    "description": "The period to wait after the last trigger reported active before scaling the resource back to 0. https://keda.sh/docs/2.9/concepts/scaling-deployments/#cooldownperiod",
                    "default": 300,
                    "type": "integer"
                },
                "offsetResetPolicy": {
                    "title": "Offset reset policy",
                    "description": "The offset reset policy for the consumer if the the consumer group is not yet subscribed to a partition.",
                    "default": "earliest",
                    "type": "string"
                },
                "minReplicas": {
                    "title": "Min replica count",
                    "description": "Minimum number of replicas KEDA will scale the resource down to. https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount",
                    "default": 0,
                    "type": "integer"
                },
                "maxReplicas": {
                    "title": "Max replica count",
                    "description": "This setting is passed to the HPA definition that KEDA will create for a given resource and holds the maximum number of replicas of the target resouce. https://keda.sh/docs/2.9/concepts/scaling-deployments/#maxreplicacount",
                    "default": 1,
                    "type": "integer"
                },
                "idleReplicas": {
                    "title": "Idle replica count",
                    "description": "If this property is set, KEDA will scale the resource down to this number of replicas. https://keda.sh/docs/2.9/concepts/scaling-deployments/#idlereplicacount",
                    "type": "integer"
                },
                "topics": {
                    "title": "Topics",
                    "description": "List of auto-generated Kafka Streams topics used by the streams app.",
                    "default": [],
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "consumerGroup",
                "lagThreshold"
            ]
        },
        "StreamsAppConfig": {
            "title": "StreamsAppConfig",
            "description": "StreamsBoostrap app configurations.\\n\\nThe attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/StreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "type": "string"
                },
                "autoscaling": {
                    "$ref": "#/definitions/StreamsAppAutoScaling"
                }
            },
            "required": [
                "streams"
            ]
        },
        "StreamsApp": {
            "title": "StreamsApp",
            "description": "StreamsApp component that configures a streams bootstrap app",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "streams-app",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/StreamsAppConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "streams-app",
                    "enum": [
                        "streams-app"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "2.9.0",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "SubPipelineComponent": {
            "title": "SubPipelineComponent",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "sub-pipeline-component",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "sub-pipeline-component",
                    "enum": [
                        "sub-pipeline-component"
                    ],
                    "type": "string"
                }
            },
            "required": [
                "name"
            ]
        },
        "SubPipelineComponentCorrect": {
            "title": "SubPipelineComponentCorrect",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "sub-pipeline-component-correct",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "sub-pipeline-component-correct",
                    "enum": [
                        "sub-pipeline-component-correct"
                    ],
                    "type": "string"
                }
            },
            "required": [
                "name"
            ]
        }
    }
}
"""

snapshots[
    "TestGenSchema.test_gen_pipeline_schema_without_custom_module test-schema-generation"
] = """{
    "title": "kpops pipeline schema",
    "type": "array",
    "items": {
        "discriminator": {
            "propertyName": "type",
            "mapping": {
                "kafka-app": "#/definitions/KafkaApp",
                "kafka-connector": "#/definitions/KafkaConnector",
                "kafka-sink-connector": "#/definitions/KafkaSinkConnector",
                "kafka-source-connector": "#/definitions/KafkaSourceConnector",
                "kubernetes-app": "#/definitions/KubernetesApp",
                "producer": "#/definitions/ProducerApp",
                "streams-app": "#/definitions/StreamsApp"
            }
        },
        "oneOf": [
            {
                "$ref": "#/definitions/KafkaApp"
            },
            {
                "$ref": "#/definitions/KafkaConnector"
            },
            {
                "$ref": "#/definitions/KafkaSinkConnector"
            },
            {
                "$ref": "#/definitions/KafkaSourceConnector"
            },
            {
                "$ref": "#/definitions/KubernetesApp"
            },
            {
                "$ref": "#/definitions/ProducerApp"
            },
            {
                "$ref": "#/definitions/StreamsApp"
            }
        ]
    },
    "definitions": {
        "InputTopicTypes": {
            "title": "InputTopicTypes",
            "description": "Input topic types\\n\\n    input (input topic), input_pattern (input pattern topic), extra (extra topic), extra_pattern (extra pattern topic).\\n    Every extra topic must have a role.\\n    ",
            "enum": [
                "input",
                "extra",
                "input-pattern",
                "extra-pattern"
            ],
            "type": "string"
        },
        "FromTopic": {
            "title": "FromTopic",
            "description": "Input topic\\n\\n:param type: Topic type\\n:type type: InputTopicTypes\\n:param role: Custom identifier belonging to a topic, provide only if `type` is `extra` or `extra-pattern`\\n:type role: str | None",
            "type": "object",
            "properties": {
                "type": {
                    "description": "Topic type",
                    "allOf": [
                        {
                            "$ref": "#/definitions/InputTopicTypes"
                        }
                    ]
                },
                "role": {
                    "title": "Role",
                    "description": "Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
                    "type": "string"
                }
            },
            "required": [
                "type"
            ],
            "additionalProperties": false
        },
        "FromSection": {
            "title": "FromSection",
            "description": "Holds multiple input topics\\n\\n:param topics: Input topics\\n:type topics: dict[str, FromTopic]",
            "type": "object",
            "properties": {
                "topics": {
                    "title": "Topics",
                    "description": "Input topics",
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    }
                }
            },
            "required": [
                "topics"
            ],
            "additionalProperties": false
        },
        "KafkaStreamsConfig": {
            "title": "KafkaStreamsConfig",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "KafkaAppConfig": {
            "title": "KafkaAppConfig",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/KafkaStreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "type": "string"
                }
            },
            "required": [
                "streams"
            ]
        },
        "OutputTopicTypes": {
            "title": "OutputTopicTypes",
            "description": "Types of output topic\\n\\n    Error (error topic), output (output topic), and extra topics. Every extra topic must have a role.\\n    ",
            "enum": [
                "error",
                "output",
                "extra"
            ],
            "type": "string"
        },
        "TopicConfig": {
            "title": "TopicConfig",
            "description": "Configure an output topic\\n\\n:param type: Topic type\\n:type type: InputTopicTypes\\n:param key_schema: Key schema class name\\n:type key_schema: str | None\\n:param partitions_count: Number of partitions into which the topic is divided\\n:type partitions_count: int | None\\n:param replication_factor: Replication topic of the topic\\n:type replication_factor: int | None\\n:param configs: Topic configs\\n:type configs: dict[str, str | int]\\n:param role: Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`\\n:type role: str | None",
            "type": "object",
            "properties": {
                "type": {
                    "description": "Topic type",
                    "allOf": [
                        {
                            "$ref": "#/definitions/OutputTopicTypes"
                        }
                    ]
                },
                "keySchema": {
                    "title": "Keyschema",
                    "description": "Key schema class name",
                    "type": "string"
                },
                "valueSchema": {
                    "title": "Valueschema",
                    "description": "Value schema class name",
                    "type": "string"
                },
                "partitions_count": {
                    "title": "Partitions Count",
                    "description": "Number of partitions into which the topic is divided",
                    "type": "integer"
                },
                "replication_factor": {
                    "title": "Replication Factor",
                    "description": "Replication topic of the topic",
                    "type": "integer"
                },
                "configs": {
                    "title": "Configs",
                    "description": "Topic configs",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "anyOf": [
                            {
                                "type": "string"
                            },
                            {
                                "type": "integer"
                            }
                        ]
                    }
                },
                "role": {
                    "title": "Role",
                    "description": "Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
                    "type": "string"
                }
            },
            "required": [
                "type"
            ],
            "additionalProperties": false
        },
        "ToSection": {
            "title": "ToSection",
            "description": "Holds multiple output topics\\n\\n:param models: Data models\\n:type models: dict[str, Any]\\n:param topics: Output topics\\n:type topics: dict[str, TopicConfig]",
            "type": "object",
            "properties": {
                "models": {
                    "title": "Models",
                    "default": {},
                    "type": "object"
                },
                "topics": {
                    "title": "Topics",
                    "description": "Output topics",
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/TopicConfig"
                    }
                }
            },
            "required": [
                "topics"
            ]
        },
        "RepoAuthFlags": {
            "title": "RepoAuthFlags",
            "type": "object",
            "properties": {
                "username": {
                    "title": "Username",
                    "type": "string"
                },
                "password": {
                    "title": "Password",
                    "type": "string"
                },
                "caFile": {
                    "title": "Cafile",
                    "type": "string",
                    "format": "path"
                },
                "insecureSkipTlsVerify": {
                    "title": "Insecureskiptlsverify",
                    "default": false,
                    "type": "boolean"
                }
            }
        },
        "HelmRepoConfig": {
            "title": "HelmRepoConfig",
            "type": "object",
            "properties": {
                "repositoryName": {
                    "title": "Repositoryname",
                    "type": "string"
                },
                "url": {
                    "title": "Url",
                    "type": "string"
                },
                "repoAuthFlags": {
                    "title": "Repoauthflags",
                    "default": {
                        "username": null,
                        "password": null,
                        "ca_file": null,
                        "insecure_skip_tls_verify": false
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/RepoAuthFlags"
                        }
                    ]
                }
            },
            "required": [
                "repositoryName",
                "url"
            ]
        },
        "KafkaApp": {
            "title": "KafkaApp",
            "description": "Base component for Kafka-based components.\\nProducer or streaming apps should inherit from this class.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-app",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaAppConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-app",
                    "enum": [
                        "kafka-app"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "2.9.0",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KafkaConnectConfig": {
            "title": "KafkaConnectConfig",
            "type": "object",
            "properties": {},
            "additionalProperties": {
                "type": "string"
            }
        },
        "KafkaConnector": {
            "title": "KafkaConnector",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-connector",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaConnectConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-connector",
                    "enum": [
                        "kafka-connector"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KafkaSinkConnector": {
            "title": "KafkaSinkConnector",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-sink-connector",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaConnectConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-sink-connector",
                    "enum": [
                        "kafka-sink-connector"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KafkaSourceConnector": {
            "title": "KafkaSourceConnector",
            "description": "Base class for all components\\n\\n:param name: Component name\\n:type name: str\\n:param from_: Topic(s) from which the component will read input\\n:type from_: FromSection | None\\n:param app: Application-specific settings\\n:type app: object | None\\n:param to: Topic(s) into which the component will write output\\n:type to: ToSection | None\\n:param prefix: Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.\\n:type prefix: str",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kafka-source-connector",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KafkaConnectConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kafka-source-connector",
                    "enum": [
                        "kafka-source-connector"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-kafka-connect-resetter",
                        "url": "https://bakdata.github.io/kafka-connect-resetter/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "offsetTopic": {
                    "title": "Offsettopic",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "KubernetesAppConfig": {
            "title": "KubernetesAppConfig",
            "type": "object",
            "properties": {}
        },
        "KubernetesApp": {
            "title": "KubernetesApp",
            "description": "Base Kubernetes app",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "kubernetes-app",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/KubernetesAppConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "kubernetes-app",
                    "enum": [
                        "kubernetes-app"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "$ref": "#/definitions/HelmRepoConfig"
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "ProducerStreamsConfig": {
            "title": "ProducerStreamsConfig",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "type": "string"
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "ProducerValues": {
            "title": "ProducerValues",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/ProducerStreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "type": "string"
                }
            },
            "required": [
                "streams"
            ]
        },
        "ProducerApp": {
            "title": "ProducerApp",
            "description": "Producer component\\n\\nThis producer holds configuration to use as values for the streams bootstrap produce helm chart.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "producer",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Producer doesn\'t support FromSection",
                    "type": "null"
                },
                "app": {
                    "$ref": "#/definitions/ProducerValues"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "producer",
                    "enum": [
                        "producer"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "2.9.0",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "StreamsConfig": {
            "title": "StreamsConfig",
            "description": "Streams Bootstrap streams section",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "type": "string"
                },
                "inputTopics": {
                    "title": "Inputtopics",
                    "default": [],
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "inputPattern": {
                    "title": "Inputpattern",
                    "type": "string"
                },
                "extraInputTopics": {
                    "title": "Extrainputtopics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "extraInputPatterns": {
                    "title": "Extrainputpatterns",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "type": "string"
                },
                "errorTopic": {
                    "title": "Errortopic",
                    "type": "string"
                },
                "config": {
                    "title": "Config",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "brokers"
            ]
        },
        "StreamsAppAutoScaling": {
            "title": "StreamsAppAutoScaling",
            "type": "object",
            "properties": {
                "enabled": {
                    "title": "Enabled",
                    "description": "Whether to enable auto-scaling using KEDA.",
                    "default": false,
                    "type": "boolean"
                },
                "consumerGroup": {
                    "title": "Consumer group",
                    "description": "Name of the consumer group used for checking the offset on the topic and processing the related lag.",
                    "type": "string"
                },
                "lagThreshold": {
                    "title": "Lag threshold",
                    "description": "Average target value to trigger scaling actions.",
                    "type": "integer"
                },
                "pollingInterval": {
                    "title": "Polling interval",
                    "description": "This is the interval to check each trigger on. https://keda.sh/docs/2.9/concepts/scaling-deployments/#pollinginterval",
                    "default": 30,
                    "type": "integer"
                },
                "cooldownPeriod": {
                    "title": "Cooldown period",
                    "description": "The period to wait after the last trigger reported active before scaling the resource back to 0. https://keda.sh/docs/2.9/concepts/scaling-deployments/#cooldownperiod",
                    "default": 300,
                    "type": "integer"
                },
                "offsetResetPolicy": {
                    "title": "Offset reset policy",
                    "description": "The offset reset policy for the consumer if the the consumer group is not yet subscribed to a partition.",
                    "default": "earliest",
                    "type": "string"
                },
                "minReplicas": {
                    "title": "Min replica count",
                    "description": "Minimum number of replicas KEDA will scale the resource down to. https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount",
                    "default": 0,
                    "type": "integer"
                },
                "maxReplicas": {
                    "title": "Max replica count",
                    "description": "This setting is passed to the HPA definition that KEDA will create for a given resource and holds the maximum number of replicas of the target resouce. https://keda.sh/docs/2.9/concepts/scaling-deployments/#maxreplicacount",
                    "default": 1,
                    "type": "integer"
                },
                "idleReplicas": {
                    "title": "Idle replica count",
                    "description": "If this property is set, KEDA will scale the resource down to this number of replicas. https://keda.sh/docs/2.9/concepts/scaling-deployments/#idlereplicacount",
                    "type": "integer"
                },
                "topics": {
                    "title": "Topics",
                    "description": "List of auto-generated Kafka Streams topics used by the streams app.",
                    "default": [],
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": [
                "consumerGroup",
                "lagThreshold"
            ]
        },
        "StreamsAppConfig": {
            "title": "StreamsAppConfig",
            "description": "StreamsBoostrap app configurations.\\n\\nThe attributes correspond to keys and values that are used as values for the streams bootstrap helm chart.",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/StreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "type": "string"
                },
                "autoscaling": {
                    "$ref": "#/definitions/StreamsAppAutoScaling"
                }
            },
            "required": [
                "streams"
            ]
        },
        "StreamsApp": {
            "title": "StreamsApp",
            "description": "StreamsApp component that configures a streams bootstrap app",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "streams-app",
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "$ref": "#/definitions/StreamsAppConfig"
                },
                "to": {
                    "title": "To",
                    "description": "Topic(s) into which the component will write output",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ]
                },
                "prefix": {
                    "title": "Prefix",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "default": "${pipeline_name}-",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "streams-app",
                    "enum": [
                        "streams-app"
                    ],
                    "type": "string"
                },
                "repoConfig": {
                    "title": "Repoconfig",
                    "default": {
                        "repository_name": "bakdata-streams-bootstrap",
                        "url": "https://bakdata.github.io/streams-bootstrap/",
                        "repo_auth_flags": {
                            "username": null,
                            "password": null,
                            "ca_file": null,
                            "insecure_skip_tls_verify": false
                        }
                    },
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "default": "2.9.0",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        }
    }
}
"""
