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
                    "default": "empty-pipeline-component",
                    "enum": [
                        "empty-pipeline-component"
                    ],
                    "title": "Component type",
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
                    "description": "Custom identifier belonging to a topic; define only if `type` is `pattern` or `None`",
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
            "title": "FromTopic",
            "type": "object"
        },
        "InputTopicTypes": {
            "description": "Input topic types\\n\\nINPUT (input topic), PATTERN (extra-topic-pattern or input-topic-pattern)",
            "enum": [
                "input",
                "pattern"
            ],
            "title": "InputTopicTypes",
            "type": "string"
        },
        "OutputTopicTypes": {
            "description": "Types of output topic\\n\\nOUTPUT (output topic), ERROR (error topic)",
            "enum": [
                "output",
                "error"
            ],
            "title": "OutputTopicTypes",
            "type": "string"
        },
        "SubPipelineComponent": {
            "description": "",
            "properties": {
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
                    "enum": [
                        "sub-pipeline-component"
                    ],
                    "title": "Component type",
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
                    "enum": [
                        "sub-pipeline-component-correct"
                    ],
                    "title": "Component type",
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
                "example_attr": {
                    "description": "Parameter description looks correct and it is not included in the class description, terminates here",
                    "title": "Example Attr",
                    "type": "string"
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
                    "default": "sub-pipeline-component-correct-docstr",
                    "description": "Newline before title is removed\\nSummarry is correctly imported. All whitespaces are removed and replaced with a single space. The description extraction terminates at the correct place, deletes 1 trailing coma",
                    "enum": [
                        "sub-pipeline-component-correct-docstr"
                    ],
                    "title": "Component type",
                    "type": "string"
                }
            },
            "required": [
                "name",
                "example_attr"
            ],
            "title": "SubPipelineComponentCorrectDocstr",
            "type": "object"
        },
        "SubPipelineComponentNoSchemaTypeNoType": {
            "description": "",
            "properties": {
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
                    "default": "sub-pipeline-component-no-schema-type-no-type",
                    "enum": [
                        "sub-pipeline-component-no-schema-type-no-type"
                    ],
                    "title": "Component type",
                    "type": "string"
                }
            },
            "required": [
                "name"
            ],
            "title": "SubPipelineComponentNoSchemaTypeNoType",
            "type": "object"
        },
        "ToSection": {
            "description": "Holds multiple output topics",
            "properties": {
                "models": {
                    "additionalProperties": {
                        "type": "string"
                    },
                    "default": {},
                    "description": "Data models",
                    "title": "Models",
                    "type": "object"
                },
                "topics": {
                    "additionalProperties": {
                        "$ref": "#/definitions/TopicConfig"
                    },
                    "default": {},
                    "description": "Output topics",
                    "title": "Topics",
                    "type": "object"
                }
            },
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
                "key_schema": {
                    "description": "Key schema class name",
                    "title": "Key schema",
                    "type": "string"
                },
                "partitions_count": {
                    "description": "Number of partitions into which the topic is divided",
                    "title": "Partitions count",
                    "type": "integer"
                },
                "replication_factor": {
                    "description": "Replication factor of the topic",
                    "title": "Replication factor",
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
                    "description": "Topic type",
                    "title": "Topic type"
                },
                "value_schema": {
                    "description": "Value schema class name",
                    "title": "Value schema",
                    "type": "string"
                }
            },
            "title": "TopicConfig",
            "type": "object"
        }
    },
    "items": {
        "discriminator": {
            "mapping": {
                "empty-pipeline-component": "#/definitions/EmptyPipelineComponent",
                "sub-pipeline-component": "#/definitions/SubPipelineComponent",
                "sub-pipeline-component-correct": "#/definitions/SubPipelineComponentCorrect",
                "sub-pipeline-component-correct-docstr": "#/definitions/SubPipelineComponentCorrectDocstr",
                "sub-pipeline-component-no-schema-type-no-type": "#/definitions/SubPipelineComponentNoSchemaTypeNoType"
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
            },
            {
                "$ref": "#/definitions/SubPipelineComponentNoSchemaTypeNoType"
            }
        ]
    },
    "title": "KPOps pipeline schema",
    "type": "array"
}
'''
