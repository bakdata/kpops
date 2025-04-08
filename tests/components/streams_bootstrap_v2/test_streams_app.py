import logging
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from lightkube.models.core_v1 import (
    PersistentVolumeClaimSpec,
    PersistentVolumeClaimStatus,
)
from lightkube.models.meta_v1 import ObjectMeta
from lightkube.resources.core_v1 import PersistentVolumeClaim
from pytest_mock import MockerFixture

from kpops.component_handlers import get_handlers
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmUpgradeInstallFlags
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.component_handlers.kubernetes.pvc_handler import PVCHandler
from kpops.components.base_components.models import TopicName
from kpops.components.base_components.models.to_section import (
    ToSection,
)
from kpops.components.common.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap_v2.streams.model import (
    PersistenceConfig,
    StreamsAppAutoScaling,
)
from kpops.components.streams_bootstrap_v2.streams.streams_app import (
    StreamsAppCleaner,
    StreamsAppV2,
)
from kpops.core.exception import ValidationError

RESOURCES_PATH = Path(__file__).parent / "resources"

STREAMS_APP_NAME = "test-streams-app-with-long-name-0123456789abcdefghijklmnop"
STREAMS_APP_FULL_NAME = "${pipeline.name}-" + STREAMS_APP_NAME
STREAMS_APP_HELM_NAME_OVERRIDE = (
    "${pipeline.name}-" + "test-streams-app-with-long-name-01234567-a35c6"
)
STREAMS_APP_RELEASE_NAME = create_helm_release_name(STREAMS_APP_FULL_NAME)
STREAMS_APP_CLEAN_FULL_NAME = STREAMS_APP_FULL_NAME + "-clean"
STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE = (
    "${pipeline.name}-" + "test-streams-app-with-long-name-01-c98c5-clean"
)
STREAMS_APP_CLEAN_RELEASE_NAME = create_helm_release_name(
    STREAMS_APP_CLEAN_FULL_NAME, "-clean"
)

log = logging.getLogger("TestStreamsApp")


@pytest.mark.filterwarnings(
    "ignore:.*StreamsBootstrapV2|StreamsAppV2.*:DeprecationWarning"
)
@pytest.mark.usefixtures("mock_env")
class TestStreamsApp:
    def test_release_name(self):
        assert STREAMS_APP_CLEAN_RELEASE_NAME.endswith("-clean")

    @pytest.fixture()
    def streams_app(self) -> StreamsAppV2:
        return StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "streams-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )

    @pytest.fixture()
    def stateful_streams_app(self) -> StreamsAppV2:
        return StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "statefulSet": True,
                    "persistence": {"enabled": True, "size": "5Gi"},
                    "streams": {
                        "brokers": "fake-broker:9092",
                    },
                },
                "to": {
                    "topics": {
                        "streams-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )

    @pytest.fixture(autouse=True)
    def empty_helm_get_values(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "get_values", return_value=None)

    def test_cleaner(self, streams_app: StreamsAppV2):
        cleaner = streams_app._cleaner
        assert isinstance(cleaner, StreamsAppCleaner)
        assert not hasattr(cleaner, "_cleaner")

    def test_cleaner_inheritance(self, streams_app: StreamsAppV2):
        streams_app.values.autoscaling = StreamsAppAutoScaling(
            enabled=True,
            consumer_group="foo",
            lag_threshold=100,
            idle_replicas=1,
        )
        assert streams_app._cleaner.values == streams_app.values

    def test_raise_validation_error_when_autoscaling_enabled_and_mandatory_fields_not_set(
        self, streams_app: StreamsAppV2
    ):
        with pytest.raises(ValidationError) as error:
            streams_app.values.autoscaling = StreamsAppAutoScaling(
                enabled=True,
            )
        msg = (
            "If app.autoscaling.enabled is set to true, "
            "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
        )
        assert str(error.value) == msg

    def test_raise_validation_error_when_autoscaling_enabled_and_only_consumer_group_set(
        self, streams_app: StreamsAppV2
    ):
        with pytest.raises(ValidationError) as error:
            streams_app.values.autoscaling = StreamsAppAutoScaling(
                enabled=True, consumer_group="a-test-group"
            )
        msg = (
            "If app.autoscaling.enabled is set to true, "
            "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
        )
        assert str(error.value) == msg

    def test_raise_validation_error_when_autoscaling_enabled_and_only_lag_threshold_is_set(
        self, streams_app: StreamsAppV2
    ):
        with pytest.raises(ValidationError) as error:
            streams_app.values.autoscaling = StreamsAppAutoScaling(
                enabled=True, lag_threshold=1000
            )
        msg = (
            "If app.autoscaling.enabled is set to true, "
            "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
        )
        assert str(error.value) == msg

    def test_cleaner_helm_release_name(self, streams_app: StreamsAppV2):
        assert (
            streams_app._cleaner.helm_release_name
            == "${pipeline.name}-test-streams-app-with-lo-c98c5-clean"
        )

    def test_cleaner_helm_name_override(self, streams_app: StreamsAppV2):
        assert (
            streams_app._cleaner.to_helm_values()["nameOverride"]
            == STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE
        )
        assert (
            streams_app._cleaner.to_helm_values()["fullnameOverride"]
            == STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE
        )

    def test_set_topics(self):
        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "example-input": {"type": "input"},
                        "b": {"type": "input"},
                        "a": {"type": "input"},
                        "topic-extra2": {"label": "role2"},
                        "topic-extra3": {"label": "role2"},
                        "topic-extra": {"label": "role1"},
                        ".*": {"type": "pattern"},
                        "example.*": {
                            "type": "pattern",
                            "label": "another-pattern",
                        },
                    }
                },
            },
        )
        assert streams_app.values.streams.input_topics == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]
        assert streams_app.values.streams.extra_input_topics == {
            "role1": [KafkaTopic(name="topic-extra")],
            "role2": [KafkaTopic(name="topic-extra2"), KafkaTopic(name="topic-extra3")],
        }
        assert streams_app.values.streams.input_pattern == ".*"
        assert streams_app.values.streams.extra_input_patterns == {
            "another-pattern": "example.*"
        }

        helm_values = streams_app.to_helm_values()
        streams_config = helm_values["streams"]
        assert streams_config["inputTopics"]
        assert "extraInputTopics" in streams_config
        assert "inputPattern" in streams_config
        assert "extraInputPatterns" in streams_config

    def test_no_empty_input_topic(self):
        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        ".*": {"type": "pattern"},
                    }
                },
            },
        )
        assert not streams_app.values.streams.extra_input_topics
        assert not streams_app.values.streams.input_topics
        assert streams_app.values.streams.input_pattern == ".*"
        assert not streams_app.values.streams.extra_input_patterns

        helm_values = streams_app.to_helm_values()
        streams_config = helm_values["streams"]
        assert "inputTopics" not in streams_config
        assert "extraInputTopics" not in streams_config
        assert "inputPattern" in streams_config
        assert "extraInputPatterns" not in streams_config

    def test_should_validate(self):
        # An exception should be raised when both label and type are defined and type is input
        with pytest.raises(
            ValueError, match="Define label only if `type` is `pattern` or `None`"
        ):
            assert StreamsAppV2.model_validate(
                {
                    "name": STREAMS_APP_NAME,
                    "namespace": "test-namespace",
                    "values": {
                        "streams": {"brokers": "fake-broker:9092"},
                    },
                    "from": {
                        "topics": {
                            "topic-input": {
                                "type": "input",
                                "label": "role",
                            }
                        }
                    },
                },
            )

        # An exception should be raised when both label and type are defined and type is error
        with pytest.raises(
            ValueError, match="Define `label` only if `type` is undefined"
        ):
            assert StreamsAppV2.model_validate(
                {
                    "name": STREAMS_APP_NAME,
                    "namespace": "test-namespace",
                    "values": {
                        "streams": {"brokers": "fake-broker:9092"},
                    },
                    "to": {
                        "topics": {
                            "topic-input": {
                                "type": "error",
                                "label": "role",
                            }
                        }
                    },
                },
            )

    def test_set_streams_output_from_to(self):
        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "streams-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "streams-app-error-topic": TopicConfig(
                            type=OutputTopicTypes.ERROR, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            label="first-extra-role",
                            partitions_count=10,
                        ),
                        "extra-topic-2": TopicConfig(
                            label="second-extra-role",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        assert streams_app.values.streams.extra_output_topics == {
            "first-extra-role": KafkaTopic(name="extra-topic-1"),
            "second-extra-role": KafkaTopic(name="extra-topic-2"),
        }
        assert streams_app.values.streams.output_topic == KafkaTopic(
            name="streams-app-output-topic"
        )
        assert streams_app.values.streams.error_topic == KafkaTopic(
            name="streams-app-error-topic"
        )

    def test_weave_inputs_from_prev_component(self):
        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
            },
        )

        streams_app.weave_from_topics(
            ToSection(
                topics={
                    TopicName("prev-output-topic"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                    TopicName("b"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                    TopicName("a"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                    TopicName("prev-error-topic"): TopicConfig(
                        type=OutputTopicTypes.ERROR, partitions_count=10
                    ),
                }
            )
        )

        assert streams_app.values.streams.input_topics == [
            KafkaTopic(name="prev-output-topic"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]

    async def test_deploy_order_when_dry_run_is_false(self, mocker: MockerFixture):
        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "streams-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "streams-app-error-topic": TopicConfig(
                            type=OutputTopicTypes.ERROR, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            label="first-extra-topic",
                            partitions_count=10,
                        ),
                        "extra-topic-2": TopicConfig(
                            label="second-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        mock = mocker.AsyncMock()
        mock_create_topic = mocker.patch.object(
            get_handlers().topic_handler, "create_topic"
        )
        mock.attach_mock(mock_create_topic, "mock_create_topic")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")

        dry_run = False
        await streams_app.deploy(dry_run=dry_run)

        assert streams_app.to
        assert streams_app.to.kafka_topics == [
            KafkaTopic(
                name="streams-app-output-topic",
                config=TopicConfig(
                    type=OutputTopicTypes.OUTPUT,
                    partitions_count=10,
                ),
            ),
            KafkaTopic(
                name="streams-app-error-topic",
                config=TopicConfig(
                    type=OutputTopicTypes.ERROR,
                    partitions_count=10,
                ),
            ),
            KafkaTopic(
                name="extra-topic-1",
                config=TopicConfig(
                    partitions_count=10,
                    label="first-extra-topic",
                ),
            ),
            KafkaTopic(
                name="extra-topic-2",
                config=TopicConfig(
                    partitions_count=10,
                    label="second-extra-topic",
                ),
            ),
        ]
        assert mock.mock_calls == [
            *(
                mocker.call.mock_create_topic(topic, dry_run=dry_run)
                for topic in streams_app.to.kafka_topics
            ),
            mocker.call.helm_upgrade_install(
                STREAMS_APP_RELEASE_NAME,
                "bakdata-streams-bootstrap/streams-app",
                dry_run,
                "test-namespace",
                {
                    "nameOverride": STREAMS_APP_HELM_NAME_OVERRIDE,
                    "fullnameOverride": STREAMS_APP_HELM_NAME_OVERRIDE,
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "extraOutputTopics": {
                            "first-extra-topic": "extra-topic-1",
                            "second-extra-topic": "extra-topic-2",
                        },
                        "outputTopic": "streams-app-output-topic",
                        "errorTopic": "streams-app-error-topic",
                    },
                },
                HelmUpgradeInstallFlags(
                    create_namespace=False,
                    force=False,
                    username=None,
                    password=None,
                    ca_file=None,
                    insecure_skip_tls_verify=False,
                    timeout="5m0s",
                    version="2.9.0",
                    wait=True,
                    wait_for_jobs=False,
                ),
            ),
        ]

    async def test_destroy(
        self,
        streams_app: StreamsAppV2,
        mocker: MockerFixture,
    ):
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")

        await streams_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", STREAMS_APP_RELEASE_NAME, True
        )

    async def test_reset_when_dry_run_is_false(
        self,
        streams_app: StreamsAppV2,
        empty_helm_get_values: MockerFixture,
        mocker: MockerFixture,
    ):
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await streams_app.reset(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace", STREAMS_APP_RELEASE_NAME, dry_run
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                "test-namespace",
                STREAMS_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__  # FIXME: why is this in the call stack?
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                STREAMS_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/streams-app-cleanup-job",
                dry_run,
                "test-namespace",
                {
                    "nameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "fullnameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "streams-app-output-topic",
                        "deleteOutput": False,
                    },
                },
                HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                "test-namespace",
                STREAMS_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    async def test_should_clean_streams_app_and_deploy_clean_up_job_and_delete_clean_up(
        self,
        streams_app: StreamsAppV2,
        empty_helm_get_values: MockerFixture,
        mocker: MockerFixture,
    ):
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await streams_app.clean(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace", STREAMS_APP_RELEASE_NAME, dry_run
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                "test-namespace",
                STREAMS_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                STREAMS_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/streams-app-cleanup-job",
                dry_run,
                "test-namespace",
                {
                    "nameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "fullnameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "streams-app-output-topic",
                        "deleteOutput": True,
                    },
                },
                HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                "test-namespace",
                STREAMS_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    async def test_should_deploy_clean_up_job_with_values_in_cluster_when_reset(
        self, mocker: MockerFixture
    ):
        image_tag_in_cluster = "1.1.1"
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/streams-app",
                "imageTag": image_tag_in_cluster,
                "nameOverride": STREAMS_APP_NAME,
                "fullnameOverride": STREAMS_APP_NAME,
                "replicaCount": 1,
                "persistence": {"enabled": False, "size": "1Gi"},
                "statefulSet": False,
                "streams": {
                    "brokers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "outputTopic": "streams-app-output-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )
        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "imageTag": "2.2.2",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "test-input-topic": {"type": "input"},
                    }
                },
                "to": {
                    "topics": {
                        "streams-app-output-topic": {"type": "output"},
                    }
                },
            },
        )

        mocker.patch.object(Helm, "uninstall")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")

        dry_run = False
        await streams_app.reset(dry_run=dry_run)

        mock_helm_upgrade_install.assert_called_once_with(
            STREAMS_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/streams-app-cleanup-job",
            dry_run,
            "test-namespace",
            {
                "image": "registry/streams-app",
                "nameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                "fullnameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                "imageTag": image_tag_in_cluster,
                "persistence": {"size": "1Gi"},
                "replicaCount": 1,
                "streams": {
                    "brokers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "outputTopic": "streams-app-output-topic",
                    "deleteOutput": False,
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
        )

    async def test_should_deploy_clean_up_job_with_values_in_cluster_when_clean(
        self, mocker: MockerFixture
    ):
        image_tag_in_cluster = "1.1.1"
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/streams-app",
                "imageTag": image_tag_in_cluster,
                "nameOverride": STREAMS_APP_NAME,
                "fullnameOverride": STREAMS_APP_NAME,
                "replicaCount": 1,
                "persistence": {"enabled": False, "size": "1Gi"},
                "statefulSet": False,
                "streams": {
                    "brokers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "outputTopic": "streams-app-output-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )
        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "imageTag": "2.2.2",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "test-input-topic": {"type": "input"},
                    }
                },
                "to": {
                    "topics": {
                        "streams-app-output-topic": {"type": "output"},
                    }
                },
            },
        )

        mock = mocker.MagicMock()
        mocker.patch.object(Helm, "uninstall")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")

        dry_run = False
        await streams_app.clean(dry_run=dry_run)

        mock_helm_upgrade_install.assert_called_once_with(
            STREAMS_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/streams-app-cleanup-job",
            dry_run,
            "test-namespace",
            {
                "image": "registry/streams-app",
                "nameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                "fullnameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                "imageTag": image_tag_in_cluster,
                "persistence": {"size": "1Gi"},
                "replicaCount": 1,
                "streams": {
                    "brokers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "outputTopic": "streams-app-output-topic",
                    "deleteOutput": True,
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
        )

    async def test_get_input_output_topics(self):
        streams_app = StreamsAppV2.model_validate(
            {
                "name": "my-app",
                "namespace": "test-namespace",
                "values": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "example-input": {"type": "input"},
                        "b": {"type": "input"},
                        "a": {"type": "input"},
                        "topic-extra2": {"label": "role2"},
                        "topic-extra3": {"label": "role2"},
                        "topic-extra": {"label": "role1"},
                        ".*": {"type": "pattern"},
                        "example.*": {
                            "type": "pattern",
                            "label": "another-pattern",
                        },
                    }
                },
                "to": {
                    "topics": {
                        "example-output": {"type": "output"},
                        "extra-topic": {"label": "fake-role"},
                    }
                },
            },
        )

        assert streams_app.values.streams.input_topics == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]
        assert streams_app.values.streams.extra_input_topics == {
            "role1": [KafkaTopic(name="topic-extra")],
            "role2": [KafkaTopic(name="topic-extra2"), KafkaTopic(name="topic-extra3")],
        }
        assert streams_app.output_topic == KafkaTopic(name="example-output")
        assert streams_app.extra_output_topics == {
            "fake-role": KafkaTopic(name="extra-topic")
        }
        assert list(streams_app.outputs) == [
            KafkaTopic(name="example-output"),
            KafkaTopic(name="extra-topic"),
        ]
        assert list(streams_app.inputs) == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
            KafkaTopic(name="topic-extra2"),
            KafkaTopic(name="topic-extra3"),
            KafkaTopic(name="topic-extra"),
        ]

    def test_raise_validation_error_when_persistence_enabled_and_size_not_set(
        self, stateful_streams_app: StreamsAppV2
    ):
        with pytest.raises(ValidationError) as error:
            stateful_streams_app.values.persistence = PersistenceConfig(
                enabled=True,
            )
        msg = (
            "If app.persistence.enabled is set to true, "
            "the field app.persistence.size needs to be set."
        )
        assert str(error.value) == msg

    @pytest.fixture()
    def pvc1(self) -> PersistentVolumeClaim:
        return PersistentVolumeClaim(
            apiVersion="v1",
            kind="PersistentVolumeClaim",
            metadata=ObjectMeta(name="test-pvc1"),
            spec=PersistentVolumeClaimSpec(),
            status=PersistentVolumeClaimStatus(),
        )

    @pytest.fixture()
    def pvc2(self) -> PersistentVolumeClaim:
        return PersistentVolumeClaim(
            apiVersion="v1",
            kind="PersistentVolumeClaim",
            metadata=ObjectMeta(name="test-pvc2"),
            spec=PersistentVolumeClaimSpec(),
            status=PersistentVolumeClaimStatus(),
        )

    @pytest.fixture()
    def pvc3(self) -> PersistentVolumeClaim:
        return PersistentVolumeClaim(
            apiVersion="v1",
            kind="PersistentVolumeClaim",
            metadata=ObjectMeta(name="test-pvc3"),
            spec=PersistentVolumeClaimSpec(),
            status=PersistentVolumeClaimStatus(),
        )

    @pytest.fixture()
    def mock_list_pvcs(
        self,
        mocker: MockerFixture,
        pvc1: PersistentVolumeClaim,
        pvc2: PersistentVolumeClaim,
        pvc3: PersistentVolumeClaim,
    ) -> MagicMock:
        async def async_generator_side_effect() -> AsyncIterator[PersistentVolumeClaim]:
            yield pvc1
            yield pvc2
            yield pvc3

        return mocker.patch.object(
            PVCHandler, "list_pvcs", side_effect=async_generator_side_effect
        )

    @pytest.mark.usefixtures("kubeconfig")
    async def test_stateful_clean_with_dry_run_false(
        self,
        stateful_streams_app: StreamsAppV2,
        empty_helm_get_values: MockerFixture,
        mock_list_pvcs: MagicMock,
        mocker: MockerFixture,
    ):
        mock = MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")
        mock_delete_pvcs = mocker.patch.object(PVCHandler, "delete_pvcs")
        mock.attach_mock(mock_delete_pvcs, "delete_pvcs")

        dry_run = False
        await stateful_streams_app.clean(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace", STREAMS_APP_RELEASE_NAME, dry_run
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                "test-namespace",
                STREAMS_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                STREAMS_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/streams-app-cleanup-job",
                dry_run,
                "test-namespace",
                {
                    "nameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "fullnameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "statefulSet": True,
                    "persistence": {"enabled": True, "size": "5Gi"},
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "streams-app-output-topic",
                        "deleteOutput": True,
                    },
                },
                HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                "test-namespace",
                STREAMS_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.delete_pvcs(False),
        ]

    @pytest.mark.usefixtures("kubeconfig")
    async def test_stateful_clean_with_dry_run_true(
        self,
        stateful_streams_app: StreamsAppV2,
        empty_helm_get_values: MockerFixture,
        mocker: MockerFixture,
        mock_list_pvcs: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.DEBUG)
        # actual component
        mocker.patch.object(stateful_streams_app, "destroy")

        cleaner = stateful_streams_app._cleaner
        assert isinstance(cleaner, StreamsAppCleaner)

        mocker.patch.object(cleaner, "destroy")
        mocker.patch.object(cleaner, "deploy")

        dry_run = True
        await stateful_streams_app.clean(dry_run=dry_run)

        mock_list_pvcs.assert_called_once()
        assert (
            f"Deleting in namespace 'test-namespace' StatefulSet '{STREAMS_APP_FULL_NAME}' PVCs ['test-pvc1', 'test-pvc2', 'test-pvc3']"
            in caplog.text
        )

    async def test_clean_should_fall_back_to_local_values_when_validation_of_cluster_values_fails(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.WARNING)

        # invalid model
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/producer-app",
                "imageTag": "1.1.1",
                "nameOverride": STREAMS_APP_NAME,
                "fullnameOverride": STREAMS_APP_NAME,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "outputTopic": "streams-app-output-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )

        streams_app = StreamsAppV2.model_validate(
            {
                "name": STREAMS_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "image": "registry/streams-app",
                    "imageTag": "2.2.2",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "test-input-topic": {"type": "input"},
                    }
                },
                "to": {
                    "topics": {
                        "streams-app-output-topic": {"type": "output"},
                    }
                },
            },
        )

        mock = mocker.MagicMock()
        mocker.patch.object(Helm, "uninstall")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")

        dry_run = False
        await streams_app.clean(dry_run=dry_run)

        assert (
            "The values in the cluster are invalid with the current model. Falling back to the enriched values of pipeline.yaml and defaults.yaml"
            in caplog.text
        )

        mock_helm_upgrade_install.assert_called_once_with(
            STREAMS_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/streams-app-cleanup-job",
            dry_run,
            "test-namespace",
            {
                "image": "registry/streams-app",
                "nameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                "fullnameOverride": STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE,
                "imageTag": "2.2.2",
                "streams": {
                    "brokers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "outputTopic": "streams-app-output-topic",
                    "deleteOutput": True,
                },
            },
            HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
        )
