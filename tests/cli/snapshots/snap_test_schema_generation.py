# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestGenSchema.test_gen_pipeline_schema_only_custom_module test-schema-generation'] = '''{
    "$defs": {
        "EmptyPipelineComponent": {
            "additionalProperties": true,
            "description": "",
            "properties": {
                "from": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/FromSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
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
                    "anyOf": [
                        {
                            "$ref": "#/$defs/ToSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Topic(s) into which the component will write output"
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
            "description": "Holds multiple input topics.",
            "properties": {
                "components": {
                    "additionalProperties": {
                        "$ref": "#/$defs/FromTopic"
                    },
                    "default": {},
                    "description": "Components to read from",
                    "title": "Components",
                    "type": "object"
                },
                "topics": {
                    "additionalProperties": {
                        "$ref": "#/$defs/FromTopic"
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
            "description": "Input topic.",
            "properties": {
                "role": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Custom identifier belonging to a topic; define only if `type` is `pattern` or `None`",
                    "title": "Role"
                },
                "type": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/InputTopicTypes"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Topic type"
                }
            },
            "title": "FromTopic",
            "type": "object"
        },
        "InputTopicTypes": {
            "description": "Input topic types.\\n\\nINPUT (input topic), PATTERN (extra-topic-pattern or input-topic-pattern)",
            "enum": [
                "input",
                "pattern"
            ],
            "title": "InputTopicTypes",
            "type": "string"
        },
        "OutputTopicTypes": {
            "description": "Types of output topic.\\n\\nOUTPUT (output topic), ERROR (error topic)",
            "enum": [
                "output",
                "error"
            ],
            "title": "OutputTopicTypes",
            "type": "string"
        },
        "SubPipelineComponent": {
            "additionalProperties": true,
            "description": "",
            "properties": {
                "from": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/FromSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
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
                    "anyOf": [
                        {
                            "$ref": "#/$defs/ToSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Topic(s) into which the component will write output"
                }
            },
            "required": [
                "name"
            ],
            "title": "SubPipelineComponent",
            "type": "object"
        },
        "SubPipelineComponentCorrect": {
            "additionalProperties": true,
            "description": "",
            "properties": {
                "from": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/FromSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
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
                    "anyOf": [
                        {
                            "$ref": "#/$defs/ToSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Topic(s) into which the component will write output"
                }
            },
            "required": [
                "name"
            ],
            "title": "SubPipelineComponentCorrect",
            "type": "object"
        },
        "SubPipelineComponentCorrectDocstr": {
            "additionalProperties": true,
            "description": "Newline before title is removed.\\nSummarry is correctly imported. All whitespaces are removed and replaced with a single space. The description extraction terminates at the correct place, deletes 1 trailing coma",
            "properties": {
                "example_attr": {
                    "description": "Parameter description looks correct and it is not included in the class description, terminates here",
                    "title": "Example Attr",
                    "type": "string"
                },
                "from": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/FromSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
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
                    "anyOf": [
                        {
                            "$ref": "#/$defs/ToSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Topic(s) into which the component will write output"
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
            "additionalProperties": true,
            "description": "",
            "properties": {
                "from": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/FromSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
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
                    "anyOf": [
                        {
                            "$ref": "#/$defs/ToSection"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Topic(s) into which the component will write output"
                }
            },
            "required": [
                "name"
            ],
            "title": "SubPipelineComponentNoSchemaTypeNoType",
            "type": "object"
        },
        "ToSection": {
            "additionalProperties": false,
            "description": "Holds multiple output topics.",
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
                        "$ref": "#/$defs/TopicConfig"
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
            "description": "Configure an output topic.",
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
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Key schema class name",
                    "title": "Key schema"
                },
                "partitions_count": {
                    "anyOf": [
                        {
                            "type": "integer"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Number of partitions into which the topic is divided",
                    "title": "Partitions count"
                },
                "replication_factor": {
                    "anyOf": [
                        {
                            "type": "integer"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Replication factor of the topic",
                    "title": "Replication factor"
                },
                "role": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Custom identifier belonging to one or multiple topics, provide only if `type` is `extra`",
                    "title": "Role"
                },
                "type": {
                    "anyOf": [
                        {
                            "$ref": "#/$defs/OutputTopicTypes"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Topic type",
                    "title": "Topic type"
                },
                "value_schema": {
                    "anyOf": [
                        {
                            "type": "string"
                        },
                        {
                            "type": "null"
                        }
                    ],
                    "default": null,
                    "description": "Value schema class name",
                    "title": "Value schema"
                }
            },
            "title": "TopicConfig",
            "type": "object"
        }
    },
    "items": {
        "discriminator": {
            "mapping": {
                "empty-pipeline-component": "#/$defs/EmptyPipelineComponent",
                "sub-pipeline-component": "#/$defs/SubPipelineComponent",
                "sub-pipeline-component-correct": "#/$defs/SubPipelineComponentCorrect",
                "sub-pipeline-component-correct-docstr": "#/$defs/SubPipelineComponentCorrectDocstr",
                "sub-pipeline-component-no-schema-type-no-type": "#/$defs/SubPipelineComponentNoSchemaTypeNoType"
            },
            "propertyName": "type"
        },
        "oneOf": [
            {
                "$ref": "#/$defs/EmptyPipelineComponent"
            },
            {
                "$ref": "#/$defs/SubPipelineComponent"
            },
            {
                "$ref": "#/$defs/SubPipelineComponentCorrect"
            },
            {
                "$ref": "#/$defs/SubPipelineComponentCorrectDocstr"
            },
            {
                "$ref": "#/$defs/SubPipelineComponentNoSchemaTypeNoType"
            }
        ]
    },
    "title": "PipelineSchema",
    "type": "array"
}
'''