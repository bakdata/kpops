# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestGenSchema.test_gen_pipeline_schema_no_modules test-schema-generation'] = ''

snapshots['TestGenSchema.test_gen_pipeline_schema_only_custom_module test-schema-generation'] = '''{
    "title": "kpops pipeline schema",
    "type": "array",
    "items": {
        "discriminator": {
            "propertyName": "type",
            "mapping": {
                "pipeline-component": "#/definitions/EmptyPipelineComponent",
                "sub-pipeline-component": "#/definitions/SubPipelineComponent",
                "sub-pipeline-component-correct": "#/definitions/SubPipelineComponentCorrect",
                "sub-pipeline-component-correct-docstr": "#/definitions/SubPipelineComponentCorrectDocstr"
            }
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
        "EmptyPipelineComponent": {
            "title": "EmptyPipelineComponent",
            "description": "",
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
        },
        "SubPipelineComponentCorrectDocstr": {
            "title": "SubPipelineComponentCorrectDocstr",
            "description": "Newline before title is removed Summarry is correctly imported. All whitespaces are removed and replaced with a single space. The description extraction terminates at the correct place, deletes trailing comas ,,",
            "type": "object",
            "properties": {
                "type": {
                    "title": "Type",
                    "description": "Parameter description looks correct and it is not included in the class description, terminates here",
                    "default": "sub-pipeline-component-correct-docstr",
                    "const": "sub-pipeline-component-correct-docstr",
                    "type": "string"
                },
                "type": {
                    "title": "Schema Type",
                    "description": "Newline before title is removed Summarry is correctly imported. All whitespaces are removed and replaced with a single space. The description extraction terminates at the correct place, deletes trailing comas ,,",
                    "default": "sub-pipeline-component-correct-docstr",
                    "enum": [
                        "sub-pipeline-component-correct-docstr"
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
'''
