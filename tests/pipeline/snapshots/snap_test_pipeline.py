# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestPipeline.test_default_config test-pipeline"] = {
    "components": [
        {
            "app": {
                "nameOverride": "resources-custom-config-app1",
                "resources": {"limits": {"memory": "2G"}, "requests": {"memory": "2G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "extraOutputTopics": {},
                    "outputTopic": "resources-custom-config-app1",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-custom-config-app1",
            "namespace": "development-namespace",
            "prefix": "resources-custom-config-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-custom-config-app1": {
                        "configs": {},
                        "partitions_count": 3,
                        "type": "output",
                    }
                },
            },
            "type": "producer",
            "version": "2.7.0",
        },
        {
            "app": {
                "image": "some-image",
                "labels": {"pipeline": "resources-custom-config"},
                "nameOverride": "resources-custom-config-app2",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "errorTopic": "resources-custom-config-app2-error",
                    "inputTopics": ["resources-custom-config-app1"],
                    "outputTopic": "resources-custom-config-app2",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-custom-config-app2",
            "namespace": "development-namespace",
            "prefix": "resources-custom-config-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-custom-config-app2": {
                        "configs": {},
                        "partitions_count": 3,
                        "type": "output",
                    },
                    "resources-custom-config-app2-error": {
                        "configs": {},
                        "partitions_count": 1,
                        "type": "error",
                    },
                },
            },
            "type": "streams-app",
            "version": "2.7.0",
        },
    ]
}

snapshots["TestPipeline.test_inflate_pipeline test-pipeline"] = {
    "components": [
        {
            "app": {
                "commandLine": {"FAKE_ARG": "fake-arg-value"},
                "image": "example-registry/fake-image",
                "imageTag": "0.0.1",
                "nameOverride": "resources-pipeline-with-inflate-scheduled-producer",
                "schedule": "30 3/8 * * *",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "extraOutputTopics": {},
                    "outputTopic": "resources-pipeline-with-inflate-scheduled-producer",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-pipeline-with-inflate-scheduled-producer",
            "namespace": "example-namespace",
            "prefix": "resources-pipeline-with-inflate-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {"com/bakdata/kafka/fake": "1.0.0"},
                "topics": {
                    "resources-pipeline-with-inflate-scheduled-producer": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 12,
                        "type": "output",
                        "valueSchema": "com.bakdata.fake.Produced",
                    }
                },
            },
            "type": "scheduled-producer",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "converter-resources-pipeline-with-inflate-converter",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 1,
                    "topics": [],
                },
                "commandLine": {"CONVERT_XML": True},
                "nameOverride": "resources-pipeline-with-inflate-converter",
                "resources": {"limits": {"memory": "2G"}, "requests": {"memory": "2G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-pipeline-with-inflate-converter-error",
                    "inputTopics": [
                        "resources-pipeline-with-inflate-scheduled-producer"
                    ],
                    "outputTopic": "resources-pipeline-with-inflate-converter",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-pipeline-with-inflate-converter",
            "namespace": "example-namespace",
            "prefix": "resources-pipeline-with-inflate-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-pipeline-with-inflate-converter": {
                        "configs": {
                            "cleanup.policy": "compact,delete",
                            "retention.ms": "-1",
                        },
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-pipeline-with-inflate-converter-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 10,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "converter",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "filter-resources-pipeline-with-inflate-should-inflate",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 4,
                    "minReplicas": 4,
                    "topics": ["resources-pipeline-with-inflate-should-inflate"],
                },
                "commandLine": {"TYPE": "nothing"},
                "image": "fake-registry/filter",
                "imageTag": "2.4.1",
                "nameOverride": "resources-pipeline-with-inflate-should-inflate",
                "replicaCount": 4,
                "resources": {"requests": {"memory": "3G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-pipeline-with-inflate-should-inflate-error",
                    "inputTopics": ["resources-pipeline-with-inflate-converter"],
                    "outputTopic": "resources-pipeline-with-inflate-should-inflate",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-pipeline-with-inflate-should-inflate",
            "namespace": "example-namespace",
            "prefix": "resources-pipeline-with-inflate-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-pipeline-with-inflate-should-inflate": {
                        "configs": {"retention.ms": "-1"},
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-pipeline-with-inflate-should-inflate-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "should-inflate",
            "version": "2.4.2",
        },
        {
            "app": {
                "batch.size": "2000",
                "behavior.on.malformed.documents": "warn",
                "behavior.on.null.values": "delete",
                "connection.compression": "true",
                "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
                "key.ignore": "false",
                "linger.ms": "5000",
                "max.buffered.records": "20000",
                "name": "sink-connector",
                "read.timeout.ms": "120000",
                "tasks.max": "1",
                "topics": "resources-pipeline-with-inflate-should-inflate",
                "transforms.changeTopic.replacement": "resources-pipeline-with-inflate-should-inflate-index-v1",
            },
            "name": "resources-pipeline-with-inflate-sink-connector",
            "namespace": "example-namespace",
            "prefix": "resources-pipeline-with-inflate-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-kafka-connect-resetter",
                "url": "https://bakdata.github.io/kafka-connect-resetter/",
            },
            "resetterValues": {},
            "to": {
                "models": {},
                "topics": {
                    "kafka-sink-connector": {"configs": {}, "type": "output"},
                    "sink-connector": {"configs": {}, "role": "test", "type": "extra"},
                },
            },
            "type": "kafka-sink-connector",
            "version": "1.0.4",
        },
    ]
}

snapshots["TestPipeline.test_kafka_connect_sink_weave_from_topics test-pipeline"] = {
    "components": [
        {
            "app": {
                "image": "fake-image",
                "nameOverride": "resources-kafka-connect-sink-streams-app",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-kafka-connect-sink-streams-app-error",
                    "inputTopics": ["example-topic"],
                    "outputTopic": "example-output",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "from": {"topics": {"example-topic": {"type": "input"}}},
            "name": "resources-kafka-connect-sink-streams-app",
            "namespace": "example-namespace",
            "prefix": "resources-kafka-connect-sink-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "example-output": {"configs": {}, "type": "output"},
                    "resources-kafka-connect-sink-streams-app-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "streams-app",
            "version": "2.4.2",
        },
        {
            "app": {
                "batch.size": "2000",
                "behavior.on.malformed.documents": "warn",
                "behavior.on.null.values": "delete",
                "connection.compression": "true",
                "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
                "key.ignore": "false",
                "linger.ms": "5000",
                "max.buffered.records": "20000",
                "name": "sink-connector",
                "read.timeout.ms": "120000",
                "tasks.max": "1",
                "topics": "example-output",
            },
            "name": "resources-kafka-connect-sink-es-sink-connector",
            "namespace": "example-namespace",
            "prefix": "resources-kafka-connect-sink-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-kafka-connect-resetter",
                "url": "https://bakdata.github.io/kafka-connect-resetter/",
            },
            "resetterValues": {},
            "type": "kafka-sink-connector",
            "version": "1.0.4",
        },
    ]
}

snapshots["TestPipeline.test_load_pipeline test-pipeline"] = {
    "components": [
        {
            "app": {
                "commandLine": {"FAKE_ARG": "fake-arg-value"},
                "image": "example-registry/fake-image",
                "imageTag": "0.0.1",
                "nameOverride": "resources-first-pipeline-scheduled-producer",
                "schedule": "30 3/8 * * *",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "extraOutputTopics": {},
                    "outputTopic": "resources-first-pipeline-scheduled-producer",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-first-pipeline-scheduled-producer",
            "namespace": "example-namespace",
            "prefix": "resources-first-pipeline-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {"com/bakdata/kafka/fake": "1.0.0"},
                "topics": {
                    "resources-first-pipeline-scheduled-producer": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 12,
                        "type": "output",
                        "valueSchema": "com.bakdata.fake.Produced",
                    }
                },
            },
            "type": "scheduled-producer",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "converter-resources-first-pipeline-converter",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 1,
                    "topics": [],
                },
                "commandLine": {"CONVERT_XML": True},
                "nameOverride": "resources-first-pipeline-converter",
                "resources": {"limits": {"memory": "2G"}, "requests": {"memory": "2G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-first-pipeline-converter-error",
                    "inputTopics": ["resources-first-pipeline-scheduled-producer"],
                    "outputTopic": "resources-first-pipeline-converter",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-first-pipeline-converter",
            "namespace": "example-namespace",
            "prefix": "resources-first-pipeline-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-first-pipeline-converter": {
                        "configs": {
                            "cleanup.policy": "compact,delete",
                            "retention.ms": "-1",
                        },
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-first-pipeline-converter-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 10,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "converter",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "filter-resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 4,
                    "minReplicas": 4,
                    "topics": [
                        "resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name"
                    ],
                },
                "commandLine": {"TYPE": "nothing"},
                "image": "fake-registry/filter",
                "imageTag": "2.4.1",
                "nameOverride": "resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name",
                "replicaCount": 4,
                "resources": {"requests": {"memory": "3G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-error",
                    "inputTopics": ["resources-first-pipeline-converter"],
                    "outputTopic": "resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name",
            "namespace": "example-namespace",
            "prefix": "resources-first-pipeline-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name": {
                        "configs": {"retention.ms": "-1"},
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-first-pipeline-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-a-long-name-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "filter",
            "version": "2.4.2",
        },
    ]
}

snapshots["TestPipeline.test_no_input_topic test-pipeline"] = {
    "components": [
        {
            "app": {
                "commandLine": {"CONVERT_XML": True},
                "nameOverride": "resources-no-input-topic-pipeline-streams-app",
                "resources": {"limits": {"memory": "2G"}, "requests": {"memory": "2G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-no-input-topic-pipeline-streams-app-error",
                    "inputPattern": ".*",
                    "outputTopic": "example-output",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "from": {"topics": {".*": {"type": "input-pattern"}}},
            "name": "resources-no-input-topic-pipeline-streams-app",
            "namespace": "example-namespace",
            "prefix": "resources-no-input-topic-pipeline-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "example-output": {"configs": {}, "type": "output"},
                    "resources-no-input-topic-pipeline-streams-app-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "streams-app",
            "version": "2.4.2",
        },
        {
            "app": {
                "nameOverride": "resources-no-input-topic-pipeline-streams-app",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-no-input-topic-pipeline-streams-app-error",
                    "extraOutputTopics": {
                        "extra": "example-output-extra",
                        "test-output": "test-output-extra",
                    },
                    "inputTopics": ["example-output"],
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-no-input-topic-pipeline-streams-app",
            "namespace": "example-namespace",
            "prefix": "resources-no-input-topic-pipeline-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "example-output-extra": {
                        "configs": {},
                        "role": "extra",
                        "type": "extra",
                    },
                    "resources-no-input-topic-pipeline-streams-app-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                    "test-output-extra": {
                        "configs": {},
                        "role": "test-output",
                        "type": "extra",
                    },
                },
            },
            "type": "streams-app",
            "version": "2.4.2",
        },
    ]
}

snapshots["TestPipeline.test_no_user_defined_components test-pipeline"] = {
    "components": [
        {
            "app": {
                "image": "fake-image",
                "nameOverride": "resources-no-user-defined-components-streams-app",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-no-user-defined-components-streams-app-error",
                    "inputTopics": ["example-topic"],
                    "outputTopic": "example-output",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "from": {"topics": {"example-topic": {"type": "input"}}},
            "name": "resources-no-user-defined-components-streams-app",
            "namespace": "example-namespace",
            "prefix": "resources-no-user-defined-components-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "example-output": {"configs": {}, "type": "output"},
                    "resources-no-user-defined-components-streams-app-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "streams-app",
            "version": "2.4.2",
        }
    ]
}

snapshots["TestPipeline.test_pipelines_with_env_values test-pipeline"] = {
    "components": [
        {
            "app": {
                "commandLine": {"FAKE_ARG": "fake-arg-value"},
                "image": "example-registry/fake-image",
                "imageTag": "0.0.1",
                "nameOverride": "resources-pipeline-with-envs-scheduled-producer",
                "schedule": "30 3/8 * * *",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "extraOutputTopics": {},
                    "outputTopic": "resources-pipeline-with-envs-scheduled-producer",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-pipeline-with-envs-scheduled-producer",
            "namespace": "example-namespace",
            "prefix": "resources-pipeline-with-envs-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {"com/bakdata/kafka/fake": "1.0.0"},
                "topics": {
                    "resources-pipeline-with-envs-scheduled-producer": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 12,
                        "type": "output",
                        "valueSchema": "com.bakdata.fake.Produced",
                    }
                },
            },
            "type": "scheduled-producer",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "converter-resources-pipeline-with-envs-converter",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 1,
                    "topics": [],
                },
                "commandLine": {"CONVERT_XML": True},
                "nameOverride": "resources-pipeline-with-envs-converter",
                "resources": {"limits": {"memory": "2G"}, "requests": {"memory": "2G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-pipeline-with-envs-converter-error",
                    "inputTopics": ["resources-pipeline-with-envs-scheduled-producer"],
                    "outputTopic": "resources-pipeline-with-envs-converter",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-pipeline-with-envs-converter",
            "namespace": "example-namespace",
            "prefix": "resources-pipeline-with-envs-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-pipeline-with-envs-converter": {
                        "configs": {
                            "cleanup.policy": "compact,delete",
                            "retention.ms": "-1",
                        },
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-pipeline-with-envs-converter-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 10,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "converter",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "filter-resources-pipeline-with-envs-filter",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 4,
                    "minReplicas": 4,
                    "topics": ["resources-pipeline-with-envs-filter"],
                },
                "commandLine": {"TYPE": "nothing"},
                "image": "fake-registry/filter",
                "imageTag": "2.4.1",
                "nameOverride": "resources-pipeline-with-envs-filter",
                "replicaCount": 4,
                "resources": {"requests": {"memory": "3G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-pipeline-with-envs-filter-error",
                    "inputTopics": ["resources-pipeline-with-envs-converter"],
                    "outputTopic": "resources-pipeline-with-envs-filter",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-pipeline-with-envs-filter",
            "namespace": "example-namespace",
            "prefix": "resources-pipeline-with-envs-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-pipeline-with-envs-filter": {
                        "configs": {"retention.ms": "-1"},
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-pipeline-with-envs-filter-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "filter",
            "version": "2.4.2",
        },
    ]
}

snapshots["TestPipeline.test_substitute_component_names test-pipeline"] = {
    "components": [
        {
            "app": {
                "commandLine": {"FAKE_ARG": "fake-arg-value"},
                "image": "example-registry/fake-image",
                "imageTag": "0.0.1",
                "labels": {
                    "app_name": "scheduled-producer",
                    "app_type": "scheduled-producer",
                },
                "nameOverride": "resources-component-type-substitution-scheduled-producer",
                "schedule": "30 3/8 * * *",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "extraOutputTopics": {},
                    "outputTopic": "resources-component-type-substitution-scheduled-producer",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-component-type-substitution-scheduled-producer",
            "namespace": "example-namespace",
            "prefix": "resources-component-type-substitution-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {"com/bakdata/kafka/fake": "1.0.0"},
                "topics": {
                    "resources-component-type-substitution-scheduled-producer": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 12,
                        "type": "output",
                        "valueSchema": "com.bakdata.fake.Produced",
                    }
                },
            },
            "type": "scheduled-producer",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "converter-resources-component-type-substitution-converter",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 1,
                    "topics": [],
                },
                "commandLine": {"CONVERT_XML": True},
                "nameOverride": "resources-component-type-substitution-converter",
                "resources": {"limits": {"memory": "2G"}, "requests": {"memory": "2G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-component-type-substitution-converter-error",
                    "inputTopics": [
                        "resources-component-type-substitution-scheduled-producer"
                    ],
                    "outputTopic": "resources-component-type-substitution-converter",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-component-type-substitution-converter",
            "namespace": "example-namespace",
            "prefix": "resources-component-type-substitution-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-component-type-substitution-converter": {
                        "configs": {
                            "cleanup.policy": "compact,delete",
                            "retention.ms": "-1",
                        },
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-component-type-substitution-converter-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 10,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "converter",
            "version": "2.4.2",
        },
        {
            "app": {
                "autoscaling": {
                    "consumergroup": "filter-resources-component-type-substitution-filter-app",
                    "enabled": True,
                    "lagThreshold": "10000",
                    "maxReplicas": 4,
                    "minReplicas": 4,
                    "topics": ["resources-component-type-substitution-filter-app"],
                },
                "commandLine": {"TYPE": "nothing"},
                "image": "fake-registry/filter",
                "imageTag": "2.4.1",
                "label": {"app_name": "filter-app", "app_type": "filter"},
                "nameOverride": "resources-component-type-substitution-filter-app",
                "replicaCount": 4,
                "resources": {"requests": {"memory": "3G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-component-type-substitution-filter-app-error",
                    "inputTopics": ["resources-component-type-substitution-converter"],
                    "outputTopic": "resources-component-type-substitution-filter-app",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-component-type-substitution-filter-app",
            "namespace": "example-namespace",
            "prefix": "resources-component-type-substitution-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "resources-component-type-substitution-filter-app": {
                        "configs": {"retention.ms": "-1"},
                        "partitions_count": 50,
                        "type": "output",
                    },
                    "resources-component-type-substitution-filter-app-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "filter",
            "version": "2.4.2",
        },
    ]
}

snapshots["TestPipeline.test_with_custom_config test-pipeline"] = {
    "components": [
        {
            "app": {
                "nameOverride": "resources-custom-config-app1",
                "resources": {"limits": {"memory": "2G"}, "requests": {"memory": "2G"}},
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "extraOutputTopics": {},
                    "outputTopic": "app1-test-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-custom-config-app1",
            "namespace": "development-namespace",
            "prefix": "resources-custom-config-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "app1-test-topic": {
                        "configs": {},
                        "partitions_count": 3,
                        "type": "output",
                    }
                },
            },
            "type": "producer",
            "version": "2.7.0",
        },
        {
            "app": {
                "image": "some-image",
                "labels": {"pipeline": "resources-custom-config"},
                "nameOverride": "resources-custom-config-app2",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "errorTopic": "app2-dead-letter-topic",
                    "inputTopics": ["app1-test-topic"],
                    "outputTopic": "app2-test-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "name": "resources-custom-config-app2",
            "namespace": "development-namespace",
            "prefix": "resources-custom-config-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "app2-dead-letter-topic": {
                        "configs": {},
                        "partitions_count": 1,
                        "type": "error",
                    },
                    "app2-test-topic": {
                        "configs": {},
                        "partitions_count": 3,
                        "type": "output",
                    },
                },
            },
            "type": "streams-app",
            "version": "2.7.0",
        },
    ]
}

snapshots["TestPipeline.test_with_env_defaults test-pipeline"] = {
    "components": [
        {
            "app": {
                "image": "fake-image",
                "nameOverride": "resources-kafka-connect-sink-streams-app-development",
                "streams": {
                    "brokers": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                    "config": {
                        "large.message.id.generator": "com.bakdata.kafka.MurmurHashIdGenerator"
                    },
                    "errorTopic": "resources-kafka-connect-sink-streams-app-development-error",
                    "inputTopics": ["example-topic"],
                    "outputTopic": "example-output",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            "from": {"topics": {"example-topic": {"type": "input"}}},
            "name": "resources-kafka-connect-sink-streams-app-development",
            "namespace": "development-namespace",
            "prefix": "resources-kafka-connect-sink-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-streams-bootstrap",
                "url": "https://bakdata.github.io/streams-bootstrap/",
            },
            "to": {
                "models": {},
                "topics": {
                    "example-output": {"configs": {}, "type": "output"},
                    "resources-kafka-connect-sink-streams-app-development-error": {
                        "configs": {"cleanup.policy": "compact,delete"},
                        "partitions_count": 1,
                        "type": "error",
                        "valueSchema": "com.bakdata.kafka.DeadLetter",
                    },
                },
            },
            "type": "streams-app",
            "version": "2.7.0",
        },
        {
            "app": {
                "batch.size": "2000",
                "behavior.on.malformed.documents": "warn",
                "behavior.on.null.values": "delete",
                "connection.compression": "true",
                "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
                "key.ignore": "false",
                "linger.ms": "5000",
                "max.buffered.records": "20000",
                "name": "sink-connector",
                "read.timeout.ms": "120000",
                "tasks.max": "1",
                "topics": "example-output",
            },
            "name": "resources-kafka-connect-sink-es-sink-connector",
            "namespace": "example-namespace",
            "prefix": "resources-kafka-connect-sink-",
            "repoConfig": {
                "repoAuthFlags": {"insecureSkipTlsVerify": False},
                "repositoryName": "bakdata-kafka-connect-resetter",
                "url": "https://bakdata.github.io/kafka-connect-resetter/",
            },
            "resetterValues": {},
            "type": "kafka-sink-connector",
            "version": "1.0.4",
        },
    ]
}
