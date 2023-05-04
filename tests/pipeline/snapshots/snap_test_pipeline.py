# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestPipeline.test_substitute_component_names test-pipeline'] = {
    'components': [
        {
            'app': {
                'commandLine': {
                    'FAKE_ARG': 'fake-arg-value'
                },
                'image': 'example-registry/fake-image',
                'imageTag': '0.0.1',
                'labels': {
                    'app_name': 'scheduled-producer',
                    'app_type': 'scheduled-producer'
                },
                'nameOverride': 'resources-component-type-substitution-scheduled-producer',
                'schedule': '30 3/8 * * *',
                'streams': {
                    'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                    'extraOutputTopics': {
                    },
                    'outputTopic': 'resources-component-type-substitution-scheduled-producer',
                    'schemaRegistryUrl': 'http://localhost:8081'
                }
            },
            'name': 'resources-component-type-substitution-scheduled-producer',
            'namespace': 'example-namespace',
            'prefix': 'resources-component-type-substitution-',
            'repoConfig': {
                'repoAuthFlags': {
                    'insecureSkipTlsVerify': False
                },
                'repositoryName': 'bakdata-streams-bootstrap',
                'url': 'https://bakdata.github.io/streams-bootstrap/'
            },
            'to': {
                'models': {
                    'com/bakdata/kafka/fake': '1.0.0'
                },
                'topics': {
                    'resources-component-type-substitution-scheduled-producer': {
                        'configs': {
                            'cleanup.policy': 'compact,delete'
                        },
                        'partitions_count': 12,
                        'type': 'output',
                        'valueSchema': 'com.bakdata.fake.Produced'
                    }
                }
            },
            'type': 'scheduled-producer',
            'version': '2.4.2'
        },
        {
            'app': {
                'autoscaling': {
                    'consumerGroup': 'converter-resources-component-type-substitution-converter',
                    'cooldownPeriod': 300,
                    'enabled': True,
                    'lagThreshold': 10000,
                    'maxReplicas': 1,
                    'minReplicas': 0,
                    'offsetResetPolicy': 'earliest',
                    'pollingInterval': 30,
                    'topics': [
                    ]
                },
                'commandLine': {
                    'CONVERT_XML': True
                },
                'nameOverride': 'resources-component-type-substitution-converter',
                'resources': {
                    'limits': {
                        'memory': '2G'
                    },
                    'requests': {
                        'memory': '2G'
                    }
                },
                'streams': {
                    'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                    'config': {
                        'large.message.id.generator': 'com.bakdata.kafka.MurmurHashIdGenerator'
                    },
                    'errorTopic': 'resources-component-type-substitution-converter-error',
                    'inputTopics': [
                        'resources-component-type-substitution-scheduled-producer'
                    ],
                    'outputTopic': 'resources-component-type-substitution-converter',
                    'schemaRegistryUrl': 'http://localhost:8081'
                }
            },
            'name': 'resources-component-type-substitution-converter',
            'namespace': 'example-namespace',
            'prefix': 'resources-component-type-substitution-',
            'repoConfig': {
                'repoAuthFlags': {
                    'insecureSkipTlsVerify': False
                },
                'repositoryName': 'bakdata-streams-bootstrap',
                'url': 'https://bakdata.github.io/streams-bootstrap/'
            },
            'to': {
                'models': {
                },
                'topics': {
                    'resources-component-type-substitution-converter': {
                        'configs': {
                            'cleanup.policy': 'compact,delete',
                            'retention.ms': '-1'
                        },
                        'partitions_count': 50,
                        'type': 'output'
                    },
                    'resources-component-type-substitution-converter-error': {
                        'configs': {
                            'cleanup.policy': 'compact,delete'
                        },
                        'partitions_count': 10,
                        'type': 'error',
                        'valueSchema': 'com.bakdata.kafka.DeadLetter'
                    }
                }
            },
            'type': 'converter',
            'version': '2.4.2'
        },
        {
            'app': {
                'autoscaling': {
                    'consumerGroup': 'filter-resources-component-type-substitution-filter-app',
                    'cooldownPeriod': 300,
                    'enabled': True,
                    'lagThreshold': 10000,
                    'maxReplicas': 4,
                    'minReplicas': 4,
                    'offsetResetPolicy': 'earliest',
                    'pollingInterval': 30,
                    'topics': [
                        'resources-component-type-substitution-filter-app'
                    ]
                },
                'commandLine': {
                    'TYPE': 'nothing'
                },
                'image': 'fake-registry/filter',
                'imageTag': '2.4.1',
                'label': {
                    'app_name': 'filter-app',
                    'app_type': 'filter'
                },
                'nameOverride': 'resources-component-type-substitution-filter-app',
                'replicaCount': 4,
                'resources': {
                    'requests': {
                        'memory': '3G'
                    }
                },
                'streams': {
                    'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                    'config': {
                        'large.message.id.generator': 'com.bakdata.kafka.MurmurHashIdGenerator'
                    },
                    'errorTopic': 'resources-component-type-substitution-filter-app-error',
                    'inputTopics': [
                        'resources-component-type-substitution-converter'
                    ],
                    'outputTopic': 'resources-component-type-substitution-filter-app',
                    'schemaRegistryUrl': 'http://localhost:8081'
                }
            },
            'name': 'resources-component-type-substitution-filter-app',
            'namespace': 'example-namespace',
            'prefix': 'resources-component-type-substitution-',
            'repoConfig': {
                'repoAuthFlags': {
                    'insecureSkipTlsVerify': False
                },
                'repositoryName': 'bakdata-streams-bootstrap',
                'url': 'https://bakdata.github.io/streams-bootstrap/'
            },
            'to': {
                'models': {
                },
                'topics': {
                    'resources-component-type-substitution-filter-app': {
                        'configs': {
                            'retention.ms': '-1'
                        },
                        'partitions_count': 50,
                        'type': 'output'
                    },
                    'resources-component-type-substitution-filter-app-error': {
                        'configs': {
                            'cleanup.policy': 'compact,delete'
                        },
                        'partitions_count': 1,
                        'type': 'error',
                        'valueSchema': 'com.bakdata.kafka.DeadLetter'
                    }
                }
            },
            'type': 'filter',
            'version': '2.4.2'
        }
    ]
}
