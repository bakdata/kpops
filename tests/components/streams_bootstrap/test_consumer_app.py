import logging
import re
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from lightkube.models.core_v1 import (
    PersistentVolumeClaim,
    PersistentVolumeClaimSpec,
    PersistentVolumeClaimStatus,
)
from lightkube.models.meta_v1 import ObjectMeta
from pydantic import ValidationError
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import (
    HelmUpgradeInstallFlags,
)
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
from kpops.components.streams_bootstrap import ConsumerApp
from kpops.components.streams_bootstrap.common.model import (
    PersistenceConfig,
    StreamsAppAutoScaling,
)
from kpops.components.streams_bootstrap.consumer.consumer_app import (
    ConsumerAppCleaner,
)

RESOURCES_PATH = Path(__file__).parent / "resources"

NAMESPACE = "test-namespace"
PREFIX = "${pipeline.name}-"
CONSUMER_APP_NAME = "test-consumer-app-with-long-name-0123456789abcdefghijklmnop"
CONSUMER_APP_FULL_NAME = PREFIX + CONSUMER_APP_NAME
CONSUMER_APP_HELM_NAME_OVERRIDE = (
    PREFIX + "test-consumer-app-with-long-name-0123456-6f3a6"
)
CONSUMER_APP_RELEASE_NAME = create_helm_release_name(CONSUMER_APP_FULL_NAME)
CONSUMER_APP_CLEAN_FULL_NAME = CONSUMER_APP_FULL_NAME + "-clean"
CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE = (
    PREFIX + "test-consumer-app-with-long-name-0-7034d-clean"
)
CONSUMER_APP_CLEAN_RELEASE_NAME = create_helm_release_name(
    CONSUMER_APP_CLEAN_FULL_NAME, "-clean"
)

log = logging.getLogger("TestConsumerApp")


@pytest.mark.usefixtures("mock_env")
class TestConsumerApp:
    def test_release_name(self) -> None:
        assert CONSUMER_APP_CLEAN_RELEASE_NAME.endswith("-clean")

    @pytest.fixture()
    def consumer_app(self) -> ConsumerApp:
        return ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
            },
        )

    @pytest.fixture()
    def stateful_consumer_app(self) -> ConsumerApp:
        return ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerApp",
                    "statefulSet": True,
                    "persistence": {
                        "enabled": True,
                        "size": "5Gi",
                        "storageClass": "foo",
                    },
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                    },
                },
            },
        )

    @pytest.fixture()
    def dry_run_handler_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.DryRunHandler"
        ).return_value

    @pytest.fixture(autouse=True)
    def empty_helm_get_values(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "get_values", return_value=None)

    def test_cleaner(self, consumer_app: ConsumerApp) -> None:
        cleaner = consumer_app._cleaner
        assert isinstance(cleaner, ConsumerAppCleaner)
        assert not hasattr(cleaner, "_cleaner")

    def test_cleaner_inheritance(self, consumer_app: ConsumerApp) -> None:
        consumer_app.values.kafka.group_id = "test-group-id"
        consumer_app.values.autoscaling = StreamsAppAutoScaling(
            enabled=True,
            lag_threshold=100,
            idle_replicas=1,
        )
        assert consumer_app._cleaner.values == consumer_app.values

    def test_cleaner_helm_release_name(self, consumer_app: ConsumerApp) -> None:
        assert (
            consumer_app._cleaner.helm_release_name
            == "${pipeline.name}-test-consumer-app-with-l-7034d-clean"
        )

    def test_cleaner_helm_name_override(self, consumer_app: ConsumerApp) -> None:
        assert (
            consumer_app._cleaner.to_helm_values()["nameOverride"]
            == CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE
        )
        assert (
            consumer_app._cleaner.to_helm_values()["fullnameOverride"]
            == CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE
        )

    def test_set_topics(self) -> None:
        consumer_app = ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
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
        assert consumer_app.values.kafka.input_topics == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]
        assert consumer_app.values.kafka.labeled_input_topics == {
            "role1": [KafkaTopic(name="topic-extra")],
            "role2": [KafkaTopic(name="topic-extra2"), KafkaTopic(name="topic-extra3")],
        }
        assert consumer_app.values.kafka.input_pattern == ".*"
        assert consumer_app.values.kafka.labeled_input_patterns == {
            "another-pattern": "example.*"
        }

        helm_values = consumer_app.to_helm_values()
        kafka_config = helm_values["kafka"]
        assert kafka_config["inputTopics"]
        assert "labeledInputTopics" in kafka_config
        assert "inputPattern" in kafka_config
        assert "labeledInputPatterns" in kafka_config

    def test_no_empty_input_topic(self) -> None:
        consumer_app = ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        ".*": {"type": "pattern"},
                    }
                },
            },
        )
        assert not consumer_app.values.kafka.labeled_input_topics
        assert not consumer_app.values.kafka.input_topics
        assert consumer_app.values.kafka.input_pattern == ".*"
        assert not consumer_app.values.kafka.labeled_input_patterns

        helm_values = consumer_app.to_helm_values()
        streams_config = helm_values["kafka"]
        assert "inputTopics" not in streams_config
        assert "extraInputTopics" not in streams_config
        assert "inputPattern" in streams_config
        assert "extraInputPatterns" not in streams_config

    def test_should_validate(self) -> None:
        # An exception should be raised when both label and type are defined and type is input
        with pytest.raises(
            ValueError, match="Define label only if `type` is `pattern` or `None`"
        ):
            assert ConsumerApp.model_validate(
                {
                    "name": CONSUMER_APP_NAME,
                    "namespace": NAMESPACE,
                    "values": {
                        "kafka": {"bootstrapServers": "fake-broker:9092"},
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

    def test_weave_inputs_from_prev_component(self) -> None:
        consumer_app = ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
            },
        )

        consumer_app.weave_from_topics(
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

        assert consumer_app.values.kafka.input_topics == [
            KafkaTopic(name="prev-output-topic"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]

    async def test_deploy_order_when_dry_run_is_false(
        self, mocker: MockerFixture
    ) -> None:
        consumer_app = ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
            },
        )
        mock_helm_upgrade_install = mocker.patch.object(
            consumer_app._helm, "upgrade_install"
        )

        mock = mocker.AsyncMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")

        dry_run = False
        await consumer_app.deploy(dry_run=dry_run)

        # Ensure no outputs are attached to a ConsumerApp deployment
        assert consumer_app.to is None

        assert mock.mock_calls == [
            mocker.call.helm_upgrade_install(
                CONSUMER_APP_RELEASE_NAME,
                "bakdata-streams-bootstrap/consumer-app",
                dry_run,
                NAMESPACE,
                {
                    "nameOverride": CONSUMER_APP_HELM_NAME_OVERRIDE,
                    "fullnameOverride": CONSUMER_APP_HELM_NAME_OVERRIDE,
                    "image": "consumerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
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
                    version="3.6.1",
                    wait=True,
                    wait_for_jobs=False,
                ),
            ),
        ]

    async def test_destroy(
        self,
        consumer_app: ConsumerApp,
        mocker: MockerFixture,
    ) -> None:
        mock_helm_uninstall = mocker.patch.object(consumer_app._helm, "uninstall")

        await consumer_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            NAMESPACE, CONSUMER_APP_RELEASE_NAME, True
        )

    async def test_reset_when_dry_run_is_false(
        self,
        consumer_app: ConsumerApp,
        empty_helm_get_values: MockerFixture,
        mocker: MockerFixture,
    ) -> None:
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await consumer_app.reset(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(NAMESPACE, CONSUMER_APP_RELEASE_NAME, dry_run),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/consumer-app-cleanup-job",
                dry_run,
                NAMESPACE,
                {
                    "nameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "fullnameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "image": "consumerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                    },
                },
                HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    async def test_should_clean_consumer_app_and_deploy_clean_up_job_and_delete_clean_up(
        self,
        consumer_app: ConsumerApp,
        empty_helm_get_values: MockerFixture,
        mocker: MockerFixture,
    ) -> None:
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await consumer_app.clean(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(NAMESPACE, CONSUMER_APP_RELEASE_NAME, dry_run),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/consumer-app-cleanup-job",
                dry_run,
                NAMESPACE,
                {
                    "nameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "fullnameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "image": "consumerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                    },
                },
                HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    async def test_should_deploy_clean_up_job_with_values_in_cluster_when_reset(
        self, mocker: MockerFixture
    ) -> None:
        image_tag_in_cluster = "1.1.1"
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/consumer-app",
                "imageTag": image_tag_in_cluster,
                "nameOverride": CONSUMER_APP_NAME,
                "fullnameOverride": CONSUMER_APP_NAME,
                "replicaCount": 1,
                "persistence": {"enabled": False, "size": "1Gi"},
                "statefulSet": False,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )
        consumer_app = ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "registry/consumer-app",
                    "imageTag": "2.2.2",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "test-input-topic": {"type": "input"},
                    }
                },
            },
        )

        mocker.patch.object(consumer_app._helm, "uninstall")

        mock_helm_upgrade_install = mocker.patch.object(
            consumer_app._cleaner._helm, "upgrade_install"
        )
        mocker.patch.object(consumer_app._cleaner._helm, "uninstall")

        dry_run = False
        await consumer_app.reset(dry_run=dry_run)

        mock_helm_upgrade_install.assert_called_once_with(
            CONSUMER_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/consumer-app-cleanup-job",
            dry_run,
            NAMESPACE,
            {
                "image": "registry/consumer-app",
                "nameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                "fullnameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                "imageTag": image_tag_in_cluster,
                "persistence": {"size": "1Gi"},
                "replicaCount": 1,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
        )

    async def test_should_deploy_clean_up_job_with_values_in_cluster_when_clean(
        self, mocker: MockerFixture
    ) -> None:
        image_tag_in_cluster = "1.1.1"
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/consumer-app",
                "imageTag": image_tag_in_cluster,
                "nameOverride": CONSUMER_APP_NAME,
                "fullnameOverride": CONSUMER_APP_NAME,
                "replicaCount": 1,
                "persistence": {"enabled": False, "size": "1Gi"},
                "statefulSet": False,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )
        consumer_app = ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "registry/consumer-app",
                    "imageTag": "2.2.2",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "test-input-topic": {"type": "input"},
                    }
                },
            },
        )

        mocker.patch.object(consumer_app._helm, "uninstall")

        mock_helm_upgrade_install = mocker.patch.object(
            consumer_app._cleaner._helm, "upgrade_install"
        )
        mocker.patch.object(consumer_app._cleaner._helm, "uninstall")

        dry_run = False
        await consumer_app.clean(dry_run=dry_run)

        mock_helm_upgrade_install.assert_called_once_with(
            CONSUMER_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/consumer-app-cleanup-job",
            dry_run,
            NAMESPACE,
            {
                "image": "registry/consumer-app",
                "nameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                "fullnameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                "imageTag": image_tag_in_cluster,
                "persistence": {"size": "1Gi"},
                "replicaCount": 1,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
        )

    async def test_get_input_topics(self) -> None:
        consumer_app = ConsumerApp.model_validate(
            {
                "name": "my-app",
                "namespace": NAMESPACE,
                "values": {
                    "image": "registry/consumer-app",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
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

        assert consumer_app.values.kafka.input_topics == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]
        assert consumer_app.values.kafka.labeled_input_topics == {
            "role1": [KafkaTopic(name="topic-extra")],
            "role2": [KafkaTopic(name="topic-extra2"), KafkaTopic(name="topic-extra3")],
        }

        # Verify no outputs are registered
        assert consumer_app.to is None
        assert not getattr(consumer_app, "outputs", None) or not list(
            consumer_app.outputs
        )

        assert list(consumer_app.inputs) == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
            KafkaTopic(name="topic-extra2"),
            KafkaTopic(name="topic-extra3"),
            KafkaTopic(name="topic-extra"),
        ]

    def test_raise_validation_error_when_persistence_enabled_and_size_not_set(
        self, stateful_consumer_app: ConsumerApp
    ) -> None:
        with pytest.raises(
            ValidationError,
            match=re.escape(
                "If app.persistence.enabled is set to true, the field app.persistence.size needs to be set."
            ),
        ):
            stateful_consumer_app.values.persistence = PersistenceConfig(enabled=True)

    def test_generate(self, stateful_consumer_app: ConsumerApp) -> None:
        assert stateful_consumer_app.generate() == {
            "helm_name_override": CONSUMER_APP_HELM_NAME_OVERRIDE,
            "helm_release_name": CONSUMER_APP_RELEASE_NAME,
            "name": CONSUMER_APP_NAME,
            "enabled": True,
            "namespace": NAMESPACE,
            "prefix": PREFIX,
            "type": "consumer-app",
            "values": {
                "image": "consumerApp",
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                },
                "persistence": {"enabled": True, "size": "5Gi", "storageClass": "foo"},
                "statefulSet": True,
            },
            "version": "3.6.1",
        }

    def test_generate_with_autoscaling_triggers(
        self, consumer_app: ConsumerApp
    ) -> None:
        consumer_app.values.autoscaling = StreamsAppAutoScaling(
            enabled=True,
            triggers=[
                {
                    "type": "cron",
                    "name": "business_hours",
                    "metadata": {
                        "timezone": "Europe/Berlin",
                        "start": "0 8 * * 1-5",
                        "end": "0 18 * * 1-5",
                        "desiredReplicas": "2",
                    },
                }
            ],
            scaling_modifiers={"formula": "business_hours", "target": "1"},
        )
        assert consumer_app.generate()["values"]["autoscaling"] == {
            "enabled": True,
            "triggers": [
                {
                    "type": "cron",
                    "name": "business_hours",
                    "metadata": {
                        "timezone": "Europe/Berlin",
                        "start": "0 8 * * 1-5",
                        "end": "0 18 * * 1-5",
                        "desiredReplicas": "2",
                    },
                }
            ],
            "scalingModifiers": {"formula": "business_hours", "target": "1"},
        }

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
        stateful_consumer_app: ConsumerApp,
        empty_helm_get_values: MockerFixture,
        mock_list_pvcs: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        mock = MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")
        mock_delete_pvcs = mocker.patch.object(PVCHandler, "delete_pvcs")
        mock.attach_mock(mock_delete_pvcs, "delete_pvcs")

        dry_run = False
        await stateful_consumer_app.clean(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(NAMESPACE, CONSUMER_APP_RELEASE_NAME, dry_run),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/consumer-app-cleanup-job",
                dry_run,
                NAMESPACE,
                {
                    "nameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "fullnameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                    "image": "consumerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                    },
                    "statefulSet": True,
                    "persistence": {
                        "enabled": True,
                        "size": "5Gi",
                        "storageClass": "foo",
                    },
                },
                HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.delete_pvcs(False),
        ]

    @pytest.mark.usefixtures("kubeconfig")
    async def test_stateful_clean_with_dry_run_true(
        self,
        stateful_consumer_app: ConsumerApp,
        empty_helm_get_values: MockerFixture,
        mocker: MockerFixture,
        mock_list_pvcs: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.DEBUG)
        # actual component
        mocker.patch.object(stateful_consumer_app, "destroy")

        cleaner = stateful_consumer_app._cleaner
        assert isinstance(cleaner, ConsumerAppCleaner)

        mocker.patch.object(cleaner, "destroy")
        mocker.patch.object(cleaner, "deploy")

        dry_run = True
        await stateful_consumer_app.clean(dry_run=dry_run)

        mock_list_pvcs.assert_called_once()
        assert (
            f"Deleting in namespace 'test-namespace' StatefulSet '{CONSUMER_APP_FULL_NAME}' PVCs ['test-pvc1', 'test-pvc2', 'test-pvc3']"
            in caplog.text
        )

    async def test_clean_should_fall_back_to_local_values_when_validation_of_cluster_values_fails(
        self,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.WARNING)

        # invalid model
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/consumer-app",
                "imageTag": "1.1.1",
                "nameOverride": CONSUMER_APP_NAME,
                "fullnameOverride": CONSUMER_APP_NAME,
                "streams": {
                    "brokers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )

        consumer_app = ConsumerApp.model_validate(
            {
                "name": CONSUMER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "registry/consumer-app",
                    "imageTag": "2.2.2",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "test-input-topic": {"type": "input"},
                    }
                },
            },
        )

        mocker.patch.object(consumer_app._helm, "uninstall")

        mock_helm_upgrade_install = mocker.patch.object(
            consumer_app._cleaner._helm, "upgrade_install"
        )
        mocker.patch.object(consumer_app._cleaner._helm, "uninstall")

        dry_run = False
        await consumer_app.clean(dry_run=dry_run)

        assert (
            "The values in the cluster are invalid with the current model. Falling back to the enriched values of pipeline.yaml and defaults.yaml"
            in caplog.text
        )

        mock_helm_upgrade_install.assert_called_once_with(
            CONSUMER_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/consumer-app-cleanup-job",
            dry_run,
            NAMESPACE,
            {
                "image": "registry/consumer-app",
                "nameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                "fullnameOverride": CONSUMER_APP_CLEAN_HELM_NAME_OVERRIDE,
                "imageTag": "2.2.2",
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "inputTopics": ["test-input-topic"],
                },
            },
            HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
        )
