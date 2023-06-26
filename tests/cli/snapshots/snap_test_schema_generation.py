# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestGenSchema.test_gen_pipeline_schema_only_custom_module test-schema-generation'] = '''{
    "definitions": {
        "EmptyPipelineComponent": {
            "description": "",
            "properties": {
                "app": {
                    "description": "Application-specific settings",
                    "title": "App"
                },
                "from": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ],
                    "description": "Topic(s) and/or components from which the component will read input",
                    "title": "From"
                },
                "name": {
                    "description": "Component name",
                    "title": "Name",
                    "type": "string"
                },
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string"
                },
                "type": {
                    "default": "pipeline-component",
                    "description": "Base class for all components",
                    "enum": [
                        "pipeline-component"
                    ],
                    "title": "Component type",
                    "type": "string"
                },
                "to": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ],
                    "description": "Topic(s) into which the component will write output",
                    "title": "To"
                },
                "type": {
                    "const": "pipeline-component",
                    "default": "pipeline-component",
                    "title": "Type",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "EmptyPipelineComponent",
            "type": "object"
        },
        "FromSection": {
            "additionalProperties": false,
            "description": "Holds multiple input topics",
            "properties": {
                "components": {
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    },
                    "default": {},
                    "description": "Components to read from",
                    "title": "Components",
                    "type": "object"
                },
                "topics": {
                    "additionalProperties": {
                        "$ref": "#/definitions/FromTopic"
                    },
                    "default": {},
                    "description": "Input topics",
                    "title": "Topics",
                    "type": "object"
                }
            },
            "title": "FromSection",
            "type": "object"
        },
        "FromTopic": {
            "additionalProperties": false,
            "description": "Input topic",
            "properties": {
                "role": {
                    "description": "Custom identifier belonging to a topic, provide only if `type` is `extra` or `extra-pattern`",
                    "title": "Role",
                    "type": "string"
                },
                "type": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/InputTopicTypes"
                        }
                    ],
                    "description": "Topic type"
                }
            },
            "required": [
                "type"
            ],
            "title": "FromTopic",
            "type": "object"
        },
        "InputTopicTypes": {
            "description": "Input topic types\\n\\ninput (input topic), input_pattern (input pattern topic), extra (extra topic), extra_pattern (extra pattern topic).\\nEvery extra topic must have a role.",
            "enum": [
                "input",
                "extra",
                "input-pattern",
                "extra-pattern"
            ],
            "title": "InputTopicTypes",
            "type": "string"
        },
        "OutputTopicTypes": {
            "description": "Types of output topic\\n\\nError (error topic), output (output topic), and extra topics. Every extra topic must have a role.",
            "enum": [
                "error",
                "output",
                "extra"
            ],
            "title": "OutputTopicTypes",
            "type": "string"
        },
        "SubPipelineComponent": {
            "description": "",
            "properties": {
                "app": {
                    "description": "Application-specific settings",
                    "title": "App"
                },
                "from": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ],
                    "description": "Topic(s) and/or components from which the component will read input",
                    "title": "From"
                },
                "name": {
                    "description": "Component name",
                    "title": "Name",
                    "type": "string"
                },
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string"
                },
                "type": {
                    "default": "sub-pipeline-component",
                    "enum": [
                        "sub-pipeline-component"
                    ],
                    "title": "Schema Type",
                    "type": "string"
                },
                "to": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ],
                    "description": "Topic(s) into which the component will write output",
                    "title": "To"
                },
                "type": {
                    "default": "sub-pipeline-component",
                    "title": "Type",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "SubPipelineComponent",
            "type": "object"
        },
        "SubPipelineComponentCorrect": {
            "description": "",
            "properties": {
                "app": {
                    "description": "Application-specific settings",
                    "title": "App"
                },
                "from": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ],
                    "description": "Topic(s) and/or components from which the component will read input",
                    "title": "From"
                },
                "name": {
                    "description": "Component name",
                    "title": "Name",
                    "type": "string"
                },
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string"
                },
                "type": {
                    "default": "sub-pipeline-component-correct",
                    "enum": [
                        "sub-pipeline-component-correct"
                    ],
                    "title": "Schema Type",
                    "type": "string"
                },
                "to": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ],
                    "description": "Topic(s) into which the component will write output",
                    "title": "To"
                },
                "type": {
                    "default": "sub-pipeline-component-correct",
                    "title": "Type",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "SubPipelineComponentCorrect",
            "type": "object"
        },
        "SubPipelineComponentCorrectDocstr": {
            "description": "Newline before title is removed\\nSummarry is correctly imported. All whitespaces are removed and replaced with a single space. The description extraction terminates at the correct place, deletes 1 trailing coma",
            "properties": {
                "app": {
                    "description": "Application-specific settings",
                    "title": "App"
                },
                "from": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/FromSection"
                        }
                    ],
                    "description": "Topic(s) and/or components from which the component will read input",
                    "title": "From"
                },
                "name": {
                    "description": "Component name",
                    "title": "Name",
                    "type": "string"
                },
                "prefix": {
                    "default": "${pipeline_name}-",
                    "description": "Pipeline prefix that will prefix every component name. If you wish to not have any prefix you can specify an empty string.",
                    "title": "Prefix",
                    "type": "string"
                },
                "type": {
                    "default": "sub-pipeline-component-correct-docstr",
                    "description": "Newline before title is removed\\nSummarry is correctly imported. All whitespaces are removed and replaced with a single space. The description extraction terminates at the correct place, deletes 1 trailing coma",
                    "enum": [
                        "sub-pipeline-component-correct-docstr"
                    ],
                    "title": "Schema Type",
                    "type": "string"
                },
                "to": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/ToSection"
                        }
                    ],
                    "description": "Topic(s) into which the component will write output",
                    "title": "To"
                },
                "type": {
                    "const": "sub-pipeline-component-correct-docstr",
                    "default": "sub-pipeline-component-correct-docstr",
                    "description": "Parameter description looks correct and it is not included in the class description, terminates here",
                    "title": "Type",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "SubPipelineComponentCorrectDocstr",
            "type": "object"
        },
        "ToSection": {
            "description": "Holds multiple output topics",
            "properties": {
                "models": {
                    "default": {},
                    "description": "Data models",
                    "title": "Models",
                    "type": "object"
                },
                "topics": {
                    "additionalProperties": {
                        "$ref": "#/definitions/TopicConfig"
                    },
                    "description": "Output topics",
                    "title": "Topics",
                    "type": "object"
                }
            },
            "required": [
                "topics"
            ],
            "title": "ToSection",
            "type": "object"
        },
        "TopicConfig": {
            "additionalProperties": false,
            "description": "Configure an output topic",
            "properties": {
                "configs": {
                    "additionalProperties": {
                        "anyOf": [
                            {
                                "type": "string"
                            },
                            {
                                "type": "integer"
                            }
                        ]
                    },
                    "default": {},
                    "description": "Topic configs",
                    "title": "Configs",
                    "type": "object"
                },
                "keySchema": {
                    "description": "Key schema class name",
                    "title": "Keyschema",
                    "type": "string"
                },
                "partitions_count": {
                    "description": "Number of partitions into which the topic is divided",
                    "title": "Partitions Count",
                    "type": "integer"
                },
                "replication_factor": {
                    "description": "Replication topic of the topic",
                    "title": "Replication Factor",
                    "type": "integer"
                },
                "role": {
                    "description": "Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
                    "title": "Role",
                    "type": "string"
                },
                "type": {
                    "allOf": [
                        {
                            "$ref": "#/definitions/OutputTopicTypes"
                        }
                    ],
                    "description": "Topic type"
                },
                "valueSchema": {
                    "description": "Value schema class name",
                    "title": "Valueschema",
                    "type": "string"
                }
            },
            "required": [
                "type"
            ],
            "title": "TopicConfig",
            "type": "object"
        }
    },
    "items": {
        "discriminator": {
            "mapping": {
                "pipeline-component": "#/definitions/EmptyPipelineComponent",
                "sub-pipeline-component": "#/definitions/SubPipelineComponent",
                "sub-pipeline-component-correct": "#/definitions/SubPipelineComponentCorrect",
                "sub-pipeline-component-correct-docstr": "#/definitions/SubPipelineComponentCorrectDocstr"
            },
            "propertyName": "type"
        },
        "oneOf": [
            {
                "$ref": "#/definitions/EmptyPipelineComponent"
            },
            {
                "$ref": "#/definitions/SubPipelineComponent"
            },
            {
                "$ref": "#/definitions/SubPipelineComponentCorrect"
            },
            {
                "$ref": "#/definitions/SubPipelineComponentCorrectDocstr"
            }
        ]
    },
    "title": "kpops pipeline schema",
    "type": "array"
}
'''
