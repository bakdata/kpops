# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestExample.test_atm_fraud atm-fraud-pipeline'] = [
    {
        'app': {
            'image': '${DOCKER_REGISTRY}/atm-demo-accountproducer',
            'imageTag': '1.0.0',
            'labels': {
                'pipeline': 'atm-fraud'
            },
            'prometheus': {
                'jmx': {
                    'enabled': False
                }
            },
            'replicaCount': 1,
            'schedule': '0 12 * * *',
            'streams': {
                'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                'extraOutputTopics': {
                },
                'optimizeLeaveGroupBehavior': False,
                'outputTopic': 'atm-fraud-account-producer-topic',
                'schemaRegistryUrl': 'http://k8kafka-cp-schema-registry.kpops.svc.cluster.local:8081/'
            },
            'suspend': True
        },
        'debug': True,
        'name': 'account-producer',
        'namespace': '${NAMESPACE}',
        'prefix': 'atm-fraud-',
        'repo_config': {
            'repo_auth_flags': {
                'insecure_skip_tls_verify': False
            },
            'repository_name': 'bakdata-streams-bootstrap',
            'url': 'https://bakdata.github.io/streams-bootstrap/'
        },
        'to': {
            'models': {
            },
            'topics': {
                'atm-fraud-account-producer-topic': {
                    'configs': {
                    },
                    'partitions_count': 3
                }
            }
        },
        'type': 'producer-app',
        'version': '2.9.0'
    },
    {
        'app': {
            'commandLine': {
                'ITERATION': 20,
                'REAL_TX': 19
            },
            'image': '${DOCKER_REGISTRY}/atm-demo-transactionavroproducer',
            'imageTag': '1.0.0',
            'labels': {
                'pipeline': 'atm-fraud'
            },
            'prometheus': {
                'jmx': {
                    'enabled': False
                }
            },
            'replicaCount': 1,
            'schedule': '0 12 * * *',
            'streams': {
                'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                'extraOutputTopics': {
                },
                'optimizeLeaveGroupBehavior': False,
                'outputTopic': 'atm-fraud-transaction-avro-producer-topic',
                'schemaRegistryUrl': 'http://k8kafka-cp-schema-registry.kpops.svc.cluster.local:8081/'
            },
            'suspend': True
        },
        'debug': True,
        'name': 'transaction-avro-producer',
        'namespace': '${NAMESPACE}',
        'prefix': 'atm-fraud-',
        'repo_config': {
            'repo_auth_flags': {
                'insecure_skip_tls_verify': False
            },
            'repository_name': 'bakdata-streams-bootstrap',
            'url': 'https://bakdata.github.io/streams-bootstrap/'
        },
        'to': {
            'models': {
            },
            'topics': {
                'atm-fraud-transaction-avro-producer-topic': {
                    'configs': {
                    },
                    'partitions_count': 3
                }
            }
        },
        'type': 'producer-app',
        'version': '2.9.0'
    },
    {
        'app': {
            'annotations': {
                'consumerGroup': 'atm-transactionjoiner-atm-fraud-joinedtransactions-topic'
            },
            'commandLine': {
                'PRODUCTIVE': False
            },
            'image': '${DOCKER_REGISTRY}/atm-demo-transactionjoiner',
            'imageTag': '1.0.0',
            'labels': {
                'pipeline': 'atm-fraud'
            },
            'prometheus': {
                'jmx': {
                    'enabled': False
                }
            },
            'replicaCount': 1,
            'streams': {
                'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                'errorTopic': 'atm-fraud-transaction-joiner-dead-letter-topic',
                'inputTopics': [
                    'atm-fraud-transaction-avro-producer-topic'
                ],
                'optimizeLeaveGroupBehavior': False,
                'outputTopic': 'atm-fraud-transaction-joiner-topic',
                'schemaRegistryUrl': 'http://k8kafka-cp-schema-registry.kpops.svc.cluster.local:8081/'
            }
        },
        'debug': True,
        'name': 'transaction-joiner',
        'namespace': '${NAMESPACE}',
        'prefix': 'atm-fraud-',
        'repo_config': {
            'repo_auth_flags': {
                'insecure_skip_tls_verify': False
            },
            'repository_name': 'bakdata-streams-bootstrap',
            'url': 'https://bakdata.github.io/streams-bootstrap/'
        },
        'to': {
            'models': {
            },
            'topics': {
                'atm-fraud-transaction-joiner-dead-letter-topic': {
                    'configs': {
                    },
                    'partitions_count': 1,
                    'type': 'error'
                },
                'atm-fraud-transaction-joiner-topic': {
                    'configs': {
                    },
                    'partitions_count': 3
                }
            }
        },
        'type': 'streams-app',
        'version': '2.9.0'
    },
    {
        'app': {
            'annotations': {
                'consumerGroup': 'atm-frauddetector-atm-fraud-possiblefraudtransactions-topic'
            },
            'commandLine': {
                'PRODUCTIVE': False
            },
            'image': '${DOCKER_REGISTRY}/atm-demo-frauddetector',
            'imageTag': '1.0.0',
            'labels': {
                'pipeline': 'atm-fraud'
            },
            'prometheus': {
                'jmx': {
                    'enabled': False
                }
            },
            'replicaCount': 1,
            'streams': {
                'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                'errorTopic': 'atm-fraud-fraud-detector-dead-letter-topic',
                'inputTopics': [
                    'atm-fraud-transaction-joiner-topic'
                ],
                'optimizeLeaveGroupBehavior': False,
                'outputTopic': 'atm-fraud-fraud-detector-topic',
                'schemaRegistryUrl': 'http://k8kafka-cp-schema-registry.kpops.svc.cluster.local:8081/'
            }
        },
        'debug': True,
        'name': 'fraud-detector',
        'namespace': '${NAMESPACE}',
        'prefix': 'atm-fraud-',
        'repo_config': {
            'repo_auth_flags': {
                'insecure_skip_tls_verify': False
            },
            'repository_name': 'bakdata-streams-bootstrap',
            'url': 'https://bakdata.github.io/streams-bootstrap/'
        },
        'to': {
            'models': {
            },
            'topics': {
                'atm-fraud-fraud-detector-dead-letter-topic': {
                    'configs': {
                    },
                    'partitions_count': 1,
                    'type': 'error'
                },
                'atm-fraud-fraud-detector-topic': {
                    'configs': {
                    },
                    'partitions_count': 3
                }
            }
        },
        'type': 'streams-app',
        'version': '2.9.0'
    },
    {
        'app': {
            'annotations': {
                'consumerGroup': 'atm-accountlinker-atm-fraud-output-topic'
            },
            'commandLine': {
                'PRODUCTIVE': False
            },
            'image': '${DOCKER_REGISTRY}/atm-demo-accountlinker',
            'imageTag': '1.0.0',
            'labels': {
                'pipeline': 'atm-fraud'
            },
            'prometheus': {
                'jmx': {
                    'enabled': False
                }
            },
            'replicaCount': 1,
            'streams': {
                'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                'errorTopic': 'atm-fraud-account-linker-dead-letter-topic',
                'extraInputTopics': {
                    'accounts': [
                        'atm-fraud-account-producer-topic'
                    ]
                },
                'inputTopics': [
                    'atm-fraud-fraud-detector-topic'
                ],
                'optimizeLeaveGroupBehavior': False,
                'outputTopic': 'atm-fraud-account-linker-topic',
                'schemaRegistryUrl': 'http://k8kafka-cp-schema-registry.kpops.svc.cluster.local:8081/'
            }
        },
        'debug': True,
        'from': {
            'components': {
                'account-producer': {
                    'role': 'accounts'
                },
                'fraud-detector': {
                    'type': 'input'
                }
            },
            'topics': {
            }
        },
        'name': 'account-linker',
        'namespace': '${NAMESPACE}',
        'prefix': 'atm-fraud-',
        'repo_config': {
            'repo_auth_flags': {
                'insecure_skip_tls_verify': False
            },
            'repository_name': 'bakdata-streams-bootstrap',
            'url': 'https://bakdata.github.io/streams-bootstrap/'
        },
        'to': {
            'models': {
            },
            'topics': {
                'atm-fraud-account-linker-dead-letter-topic': {
                    'configs': {
                    },
                    'partitions_count': 1,
                    'type': 'error'
                },
                'atm-fraud-account-linker-topic': {
                    'configs': {
                    },
                    'partitions_count': 3
                }
            }
        },
        'type': 'streams-app',
        'version': '2.9.0'
    },
    {
        '_resetter': {
            'app': {
                'config': {
                    'brokers': 'http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092',
                    'connector': 'atm-fraud-postgresql-connector'
                },
                'connectorType': 'sink'
            },
            'name': 'postgresql-connector',
            'namespace': '${NAMESPACE}',
            'prefix': 'atm-fraud-',
            'repo_config': {
                'repo_auth_flags': {
                    'insecure_skip_tls_verify': False
                },
                'repository_name': 'bakdata-kafka-connect-resetter',
                'url': 'https://bakdata.github.io/kafka-connect-resetter/'
            },
            'suffix': '-clean',
            'type': 'kafka-connector-resetter',
            'version': '1.0.4'
        },
        'app': {
            'auto.create': True,
            'connection.ds.pool.size': 5,
            'connection.password': 'AppPassword',
            'connection.url': 'jdbc:postgresql://postgresql-dev.${NAMESPACE}.svc.cluster.local:5432/app_db',
            'connection.user': 'app1',
            'connector.class': 'io.confluent.connect.jdbc.JdbcSinkConnector',
            'errors.deadletterqueue.context.headers.enable': True,
            'errors.deadletterqueue.topic.name': 'postgres-request-sink-dead-letters',
            'errors.deadletterqueue.topic.replication.factor': 1,
            'errors.tolerance': 'all',
            'insert.mode': 'insert',
            'insert.mode.databaselevel': True,
            'key.converter': 'org.apache.kafka.connect.storage.StringConverter',
            'name': 'atm-fraud-postgresql-connector',
            'pk.mode': 'record_value',
            'table.name.format': 'fraud_transactions',
            'tasks.max': 1,
            'topics': 'atm-fraud-account-linker-topic',
            'transforms': 'flatten',
            'transforms.flatten.type': 'org.apache.kafka.connect.transforms.Flatten$Value',
            'value.converter': 'io.confluent.connect.avro.AvroConverter',
            'value.converter.schema.registry.url': 'http://k8kafka-cp-schema-registry.${NAMESPACE}.svc.cluster.local:8081'
        },
        'name': 'postgresql-connector',
        'prefix': 'atm-fraud-',
        'resetter_values': {
        },
        'type': 'kafka-sink-connector'
    }
]
