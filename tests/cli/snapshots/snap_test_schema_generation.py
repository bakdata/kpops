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
                "pipeline-component": "#/definitions/PipelineComponent",
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
                "$ref": "#/definitions/PipelineComponent"
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
            "description": "Input topic",
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
                    "description": "Custom identifier belonging to a topic, provide only if `type` is `extra` or `extra-pattern`",
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
            "description": "Holds multiple input topics",
            "type": "object",
            "properties": {
                "topics": {
                    "title": "Topics",
                    "description": "Input topics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    }
                },
                "components": {
                    "title": "Components",
                    "description": "Components to read from",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    }
                }
            },
            "additionalProperties": false
        },
        "KafkaStreamsConfig": {
            "title": "KafkaStreamsConfig",
            "description": "Kafka Streams config",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "description": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "description": "URL of the schema registry",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "KafkaAppConfig": {
            "title": "KafkaAppConfig",
            "description": "Settings specific to Kafka Apps",
            "type": "object",
            "properties": {
                "streams": {
                    "title": "Streams",
                    "description": "Kafka streams config",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaStreamsConfig"
                        }
                    ]
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "description": "Override name with this value",
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
            "description": "Configure an output topic",
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
            "description": "Holds multiple output topics",
            "type": "object",
            "properties": {
                "models": {
                    "title": "Models",
                    "description": "Data models",
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
            "description": "Authorisation-related flags for `helm repo`",
            "type": "object",
            "properties": {
                "username": {
                    "title": "Username",
                    "description": "Username",
                    "type": "string"
                },
                "password": {
                    "title": "Password",
                    "description": "Password",
                    "type": "string"
                },
                "caFile": {
                    "title": "Cafile",
                    "description": "Certificate file",
                    "type": "string",
                    "format": "path"
                },
                "insecureSkipTlsVerify": {
                    "title": "Insecureskiptlsverify",
                    "description": "If true, Kubernetes API server\'s certificate will not be checked for validity",
                    "default": false,
                    "type": "boolean"
                }
            }
        },
        "HelmRepoConfig": {
            "title": "HelmRepoConfig",
            "description": "Helm repository configuration",
            "type": "object",
            "properties": {
                "repositoryName": {
                    "title": "Repositoryname",
                    "description": "Name of the Helm repository",
                    "type": "string"
                },
                "url": {
                    "title": "Url",
                    "description": "URL to the Helm repository",
                    "type": "string"
                },
                "repoAuthFlags": {
                    "title": "Repoauthflags",
                    "description": "Authorisation-related flags",
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
            "description": "Base component for Kafka-based components. Producer or streaming apps should inherit from this class.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-app",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base component for Kafka-based components. Producer or streaming apps should inherit from this class.",
                    "default": "kafka-app",
                    "enum": [
                        "kafka-app"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaAppConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
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
            "description": "Settings specific to Kafka Connectors",
            "type": "object",
            "properties": {},
            "additionalProperties": {
                "type": "string"
            }
        },
        "KafkaConnector": {
            "title": "KafkaConnector",
            "description": "Base class for all Kafka connectors Should only be used to set defaults",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-connector",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base class for all Kafka connectors Should only be used to set defaults",
                    "default": "kafka-connector",
                    "enum": [
                        "kafka-connector"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaConnectConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "default": "1.0.4",
                    "type": "string"
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
            "description": "Kafka sink connector model",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-sink-connector",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Kafka sink connector model",
                    "default": "kafka-sink-connector",
                    "enum": [
                        "kafka-sink-connector"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaConnectConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "default": "1.0.4",
                    "type": "string"
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
            "description": "Kafka source connector model",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-source-connector",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Kafka source connector model",
                    "default": "kafka-source-connector",
                    "enum": [
                        "kafka-source-connector"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaConnectConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "offsetTopic": {
                    "title": "Offsettopic",
                    "description": "offset.storage.topic, more info: https://kafka.apache.org/documentation/#connect_running",
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
            "description": "Settings specific to Kubernetes Apps",
            "type": "object",
            "properties": {}
        },
        "KubernetesApp": {
            "title": "KubernetesApp",
            "description": "Base class for all Kubernetes apps. All built-in components are Kubernetes apps, except for the Kafka connectors.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kubernetes-app",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base class for all Kubernetes apps. All built-in components are Kubernetes apps, except for the Kafka connectors.",
                    "default": "kubernetes-app",
                    "enum": [
                        "kubernetes-app"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KubernetesAppConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "PipelineComponent": {
            "title": "PipelineComponent",
            "description": "Base class for all components",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "pipeline-component",
                    "const": "pipeline-component",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base class for all components",
                    "default": "pipeline-component",
                    "enum": [
                        "pipeline-component"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
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
                }
            },
            "required": [
                "name"
            ]
        },
        "ProducerStreamsConfig": {
            "title": "ProducerStreamsConfig",
            "description": "Kafka Streams settings specific to Producer",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "description": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "description": "URL of the schema registry",
                    "type": "string"
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "description": "Extra output topics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "description": "Output topic",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "ProducerValues": {
            "title": "ProducerValues",
            "description": "Settings specific to Producers",
            "type": "object",
            "properties": {
                "streams": {
                    "title": "Streams",
                    "description": "Kafka Streams settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ProducerStreamsConfig"
                        }
                    ]
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "description": "Override name with this value",
                    "type": "string"
                }
            },
            "required": [
                "streams"
            ]
        },
        "ProducerApp": {
            "title": "ProducerApp",
            "description": "Producer component This producer holds configuration to use as values for the streams bootstrap producer helm chart.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "producer",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Producer component This producer holds configuration to use as values for the streams bootstrap producer helm chart.",
                    "default": "producer",
                    "enum": [
                        "producer"
                    ],
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
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ProducerValues"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
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
                    "description": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "description": "URL of the schema registry",
                    "type": "string"
                },
                "inputTopics": {
                    "title": "Inputtopics",
                    "description": "Input topics",
                    "default": [],
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "inputPattern": {
                    "title": "Inputpattern",
                    "description": "Input pattern",
                    "type": "string"
                },
                "extraInputTopics": {
                    "title": "Extrainputtopics",
                    "description": "Extra input topics",
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
                    "description": "Extra input patterns",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "description": "Extra output topics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "description": "Output topic",
                    "type": "string"
                },
                "errorTopic": {
                    "title": "Errortopic",
                    "description": "Error topic",
                    "type": "string"
                },
                "config": {
                    "title": "Config",
                    "description": "Configuration",
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
            "description": "Kubernetes Event-driven Autoscaling config",
            "type": "object",
            "properties": {
                "enabled": {
                    "title": "Enabled",
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
                    "description": "The offset reset policy for the consumer if the consumer group is not yet subscribed to a partition.",
                    "default": "earliest",
                    "type": "string"
                },
                "minReplicas": {
                    "title": "Min replica count",
                    "description": "Minimum number of replicas KEDA will scale the resource down to. \\"https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount\\"",
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
            "description": "StreamsBoostrap app configurations. The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart. :params streams: Streams Bootstrap streams section",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/StreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "description": "Override name with this value",
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
                    "description": "Component type",
                    "default": "streams-app",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "StreamsApp component that configures a streams bootstrap app",
                    "default": "streams-app",
                    "enum": [
                        "streams-app"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/StreamsAppConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
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
            "description": "",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "sub-pipeline-component",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "sub-pipeline-component",
                    "enum": [
                        "sub-pipeline-component"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
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
                }
            },
            "required": [
                "name"
            ]
        },
        "SubPipelineComponentCorrect": {
            "title": "SubPipelineComponentCorrect",
            "description": "",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "sub-pipeline-component-correct",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "default": "sub-pipeline-component-correct",
                    "enum": [
                        "sub-pipeline-component-correct"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
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
                "pipeline-component": "#/definitions/PipelineComponent",
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
                "$ref": "#/definitions/PipelineComponent"
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
            "description": "Input topic",
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
                    "description": "Custom identifier belonging to a topic, provide only if `type` is `extra` or `extra-pattern`",
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
            "description": "Holds multiple input topics",
            "type": "object",
            "properties": {
                "topics": {
                    "title": "Topics",
                    "description": "Input topics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    }
                },
                "components": {
                    "title": "Components",
                    "description": "Components to read from",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    }
                }
            },
            "additionalProperties": false
        },
        "KafkaStreamsConfig": {
            "title": "KafkaStreamsConfig",
            "description": "Kafka Streams config",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "description": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "description": "URL of the schema registry",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "KafkaAppConfig": {
            "title": "KafkaAppConfig",
            "description": "Settings specific to Kafka Apps",
            "type": "object",
            "properties": {
                "streams": {
                    "title": "Streams",
                    "description": "Kafka streams config",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaStreamsConfig"
                        }
                    ]
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "description": "Override name with this value",
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
            "description": "Configure an output topic",
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
            "description": "Holds multiple output topics",
            "type": "object",
            "properties": {
                "models": {
                    "title": "Models",
                    "description": "Data models",
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
            "description": "Authorisation-related flags for `helm repo`",
            "type": "object",
            "properties": {
                "username": {
                    "title": "Username",
                    "description": "Username",
                    "type": "string"
                },
                "password": {
                    "title": "Password",
                    "description": "Password",
                    "type": "string"
                },
                "caFile": {
                    "title": "Cafile",
                    "description": "Certificate file",
                    "type": "string",
                    "format": "path"
                },
                "insecureSkipTlsVerify": {
                    "title": "Insecureskiptlsverify",
                    "description": "If true, Kubernetes API server\'s certificate will not be checked for validity",
                    "default": false,
                    "type": "boolean"
                }
            }
        },
        "HelmRepoConfig": {
            "title": "HelmRepoConfig",
            "description": "Helm repository configuration",
            "type": "object",
            "properties": {
                "repositoryName": {
                    "title": "Repositoryname",
                    "description": "Name of the Helm repository",
                    "type": "string"
                },
                "url": {
                    "title": "Url",
                    "description": "URL to the Helm repository",
                    "type": "string"
                },
                "repoAuthFlags": {
                    "title": "Repoauthflags",
                    "description": "Authorisation-related flags",
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
            "description": "Base component for Kafka-based components. Producer or streaming apps should inherit from this class.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-app",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base component for Kafka-based components. Producer or streaming apps should inherit from this class.",
                    "default": "kafka-app",
                    "enum": [
                        "kafka-app"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaAppConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
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
            "description": "Settings specific to Kafka Connectors",
            "type": "object",
            "properties": {},
            "additionalProperties": {
                "type": "string"
            }
        },
        "KafkaConnector": {
            "title": "KafkaConnector",
            "description": "Base class for all Kafka connectors Should only be used to set defaults",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-connector",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base class for all Kafka connectors Should only be used to set defaults",
                    "default": "kafka-connector",
                    "enum": [
                        "kafka-connector"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaConnectConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "default": "1.0.4",
                    "type": "string"
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
            "description": "Kafka sink connector model",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-sink-connector",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Kafka sink connector model",
                    "default": "kafka-sink-connector",
                    "enum": [
                        "kafka-sink-connector"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaConnectConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "default": "1.0.4",
                    "type": "string"
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
            "description": "Kafka source connector model",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kafka-source-connector",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Kafka source connector model",
                    "default": "kafka-source-connector",
                    "enum": [
                        "kafka-source-connector"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KafkaConnectConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "resetterValues": {
                    "title": "Resettervalues",
                    "description": "Overriding Kafka Connect Resetter Helm values. E.g. to override the Image Tag etc.",
                    "type": "object"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "default": "1.0.4",
                    "type": "string"
                },
                "offsetTopic": {
                    "title": "Offsettopic",
                    "description": "offset.storage.topic, more info: https://kafka.apache.org/documentation/#connect_running",
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
            "description": "Settings specific to Kubernetes Apps",
            "type": "object",
            "properties": {}
        },
        "KubernetesApp": {
            "title": "KubernetesApp",
            "description": "Base class for all Kubernetes apps. All built-in components are Kubernetes apps, except for the Kafka connectors.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "kubernetes-app",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base class for all Kubernetes apps. All built-in components are Kubernetes apps, except for the Kafka connectors.",
                    "default": "kubernetes-app",
                    "enum": [
                        "kubernetes-app"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/KubernetesAppConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
                    "allOf": [
                        {
                            "$ref": "#/definitions/HelmRepoConfig"
                        }
                    ]
                },
                "namespace": {
                    "title": "Namespace",
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "app",
                "namespace"
            ]
        },
        "PipelineComponent": {
            "title": "PipelineComponent",
            "description": "Base class for all components",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "default": "pipeline-component",
                    "const": "pipeline-component",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Base class for all components",
                    "default": "pipeline-component",
                    "enum": [
                        "pipeline-component"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
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
                }
            },
            "required": [
                "name"
            ]
        },
        "ProducerStreamsConfig": {
            "title": "ProducerStreamsConfig",
            "description": "Kafka Streams settings specific to Producer",
            "type": "object",
            "properties": {
                "brokers": {
                    "title": "Brokers",
                    "description": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "description": "URL of the schema registry",
                    "type": "string"
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "description": "Extra output topics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "description": "Output topic",
                    "type": "string"
                }
            },
            "required": [
                "brokers"
            ]
        },
        "ProducerValues": {
            "title": "ProducerValues",
            "description": "Settings specific to Producers",
            "type": "object",
            "properties": {
                "streams": {
                    "title": "Streams",
                    "description": "Kafka Streams settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ProducerStreamsConfig"
                        }
                    ]
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "description": "Override name with this value",
                    "type": "string"
                }
            },
            "required": [
                "streams"
            ]
        },
        "ProducerApp": {
            "title": "ProducerApp",
            "description": "Producer component This producer holds configuration to use as values for the streams bootstrap producer helm chart.",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Component type",
                    "default": "producer",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "Producer component This producer holds configuration to use as values for the streams bootstrap producer helm chart.",
                    "default": "producer",
                    "enum": [
                        "producer"
                    ],
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
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/ProducerValues"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
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
                    "description": "Brokers",
                    "type": "string"
                },
                "schemaRegistryUrl": {
                    "title": "Schemaregistryurl",
                    "description": "URL of the schema registry",
                    "type": "string"
                },
                "inputTopics": {
                    "title": "Inputtopics",
                    "description": "Input topics",
                    "default": [],
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "inputPattern": {
                    "title": "Inputpattern",
                    "description": "Input pattern",
                    "type": "string"
                },
                "extraInputTopics": {
                    "title": "Extrainputtopics",
                    "description": "Extra input topics",
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
                    "description": "Extra input patterns",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "extraOutputTopics": {
                    "title": "Extraoutputtopics",
                    "description": "Extra output topics",
                    "default": {},
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "outputTopic": {
                    "title": "Outputtopic",
                    "description": "Output topic",
                    "type": "string"
                },
                "errorTopic": {
                    "title": "Errortopic",
                    "description": "Error topic",
                    "type": "string"
                },
                "config": {
                    "title": "Config",
                    "description": "Configuration",
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
            "description": "Kubernetes Event-driven Autoscaling config",
            "type": "object",
            "properties": {
                "enabled": {
                    "title": "Enabled",
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
                    "description": "The offset reset policy for the consumer if the consumer group is not yet subscribed to a partition.",
                    "default": "earliest",
                    "type": "string"
                },
                "minReplicas": {
                    "title": "Min replica count",
                    "description": "Minimum number of replicas KEDA will scale the resource down to. \\"https://keda.sh/docs/2.9/concepts/scaling-deployments/#minreplicacount\\"",
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
            "description": "StreamsBoostrap app configurations. The attributes correspond to keys and values that are used as values for the streams bootstrap helm chart. :params streams: Streams Bootstrap streams section",
            "type": "object",
            "properties": {
                "streams": {
                    "$ref": "#/definitions/StreamsConfig"
                },
                "nameOverride": {
                    "title": "Nameoverride",
                    "description": "Override name with this value",
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
                    "description": "Component type",
                    "default": "streams-app",
                    "type": "string"
                },
                "type": {
                    "title": "Component type",
                    "description": "StreamsApp component that configures a streams bootstrap app",
                    "default": "streams-app",
                    "enum": [
                        "streams-app"
                    ],
                    "type": "string"
                },
                "name": {
                    "title": "Name",
                    "description": "Component name",
                    "type": "string"
                },
                "from": {
                    "title": "From",
                    "description": "Topic(s) and/or components from which the component will read input",
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ]
                },
                "app": {
                    "title": "App",
                    "description": "Application-specific settings",
                    "allOf": [
                        {
                            "$ref": "#/definitions/StreamsAppConfig"
                        }
                    ]
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
                "repoConfig": {
                    "title": "Repoconfig",
                    "description": "Configuration of the Helm chart repo to be used for deploying the component",
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
                    "description": "Namespace in which the component shall be deployed",
                    "type": "string"
                },
                "version": {
                    "title": "Version",
                    "description": "Helm chart version",
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
