import re
from collections.abc import AsyncIterator
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
from structlog.testing import capture_logs

from kpops.component_handlers import get_handlers
from kpops.component_handlers.helm.helm import Helm
from kpops.component_handlers.helm.model import HelmUpgradeInstallFlags
from kpops.component_handlers.helm.utils import create_helm_release_name
from kpops.component_handlers.kubernetes.pvc_handler import PVCHandler
from kpops.components.base_components.models import TopicName
from kpops.components.base_components.models.to_section import ToSection
from kpops.components.common.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap import ConsumerProducerApp
from kpops.components.streams_bootstrap.common.model import (
    PersistenceConfig,
    StreamsAppAutoScaling,
)
from kpops.components.streams_bootstrap.consumer_producer.consumer_producer_app import (
    ConsumerProducerAppCleaner,
)

NAMESPACE = "test-namespace"
PREFIX = "${pipeline.name}-"
CONSUMER_PRODUCER_APP_NAME = "test-consumer-producer-app"
CONSUMER_PRODUCER_APP_FULL_NAME = PREFIX + CONSUMER_PRODUCER_APP_NAME
CONSUMER_PRODUCER_APP_RELEASE_NAME = create_helm_release_name(
    CONSUMER_PRODUCER_APP_FULL_NAME
)
CONSUMER_PRODUCER_APP_CLEAN_FULL_NAME = CONSUMER_PRODUCER_APP_FULL_NAME + "-clean"
CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME = create_helm_release_name(
    CONSUMER_PRODUCER_APP_CLEAN_FULL_NAME, "-clean"
)


@pytest.mark.usefixtures("mock_env")
class TestConsumerProducerApp:
    @pytest.fixture()
    def consumer_producer_app(self) -> ConsumerProducerApp:
        return ConsumerProducerApp.model_validate(
            {
                "name": CONSUMER_PRODUCER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerproducerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "consumer-producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )

    @pytest.fixture()
    def stateful_consumer_producer_app(self) -> ConsumerProducerApp:
        return ConsumerProducerApp.model_validate(
            {
                "name": CONSUMER_PRODUCER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerproducerApp",
                    "statefulSet": True,
                    "persistence": {
                        "enabled": True,
                        "size": "5Gi",
                        "storageClass": "foo",
                    },
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "consumer-producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )

    @pytest.fixture(autouse=True)
    def empty_helm_get_values(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "get_values", return_value=None)

    def test_cleaner(self, consumer_producer_app: ConsumerProducerApp) -> None:
        cleaner = consumer_producer_app._cleaner
        assert isinstance(cleaner, ConsumerProducerAppCleaner)
        assert not hasattr(cleaner, "_cleaner")

    def test_cleaner_inheritance(
        self, consumer_producer_app: ConsumerProducerApp
    ) -> None:
        consumer_producer_app.values.kafka.group_id = "test-group-id"
        consumer_producer_app.values.autoscaling = StreamsAppAutoScaling(
            enabled=True,
            lag_threshold=100,
            idle_replicas=1,
        )
        assert consumer_producer_app._cleaner.values == consumer_producer_app.values

    def test_cleaner_helm_release_name(
        self, consumer_producer_app: ConsumerProducerApp
    ) -> None:
        assert (
            consumer_producer_app._cleaner.helm_release_name
            == CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME
        )

    def test_helm_charts(self, consumer_producer_app: ConsumerProducerApp) -> None:
        assert (
            consumer_producer_app.helm_chart
            == "bakdata-streams-bootstrap/consumerproducer-app"
        )
        assert (
            consumer_producer_app._cleaner.helm_chart
            == "bakdata-streams-bootstrap/consumerproducer-app-cleanup-job"
        )

    def test_set_topics(self) -> None:
        consumer_producer_app = ConsumerProducerApp.model_validate(
            {
                "name": CONSUMER_PRODUCER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerproducerApp",
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
        assert consumer_producer_app.values.kafka.input_topics == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]
        assert consumer_producer_app.values.kafka.labeled_input_topics == {
            "role1": [KafkaTopic(name="topic-extra")],
            "role2": [KafkaTopic(name="topic-extra2"), KafkaTopic(name="topic-extra3")],
        }
        assert consumer_producer_app.values.kafka.input_pattern == ".*"
        assert consumer_producer_app.values.kafka.labeled_input_patterns == {
            "another-pattern": "example.*"
        }

        kafka_config = consumer_producer_app.to_helm_values()["kafka"]
        assert kafka_config["inputTopics"]
        assert "labeledInputTopics" in kafka_config
        assert "inputPattern" in kafka_config
        assert "labeledInputPatterns" in kafka_config

    def test_set_output_topics_from_to(self) -> None:
        consumer_producer_app = ConsumerProducerApp.model_validate(
            {
                "name": CONSUMER_PRODUCER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerproducerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "consumer-producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "consumer-producer-app-error-topic": TopicConfig(
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
        assert consumer_producer_app.values.kafka.labeled_output_topics == {
            "first-extra-role": KafkaTopic(name="extra-topic-1"),
            "second-extra-role": KafkaTopic(name="extra-topic-2"),
        }
        assert consumer_producer_app.values.kafka.output_topic == KafkaTopic(
            name="consumer-producer-app-output-topic"
        )
        assert consumer_producer_app.values.kafka.error_topic == KafkaTopic(
            name="consumer-producer-app-error-topic"
        )

    def test_weave_inputs_from_prev_component(self) -> None:
        consumer_producer_app = ConsumerProducerApp.model_validate(
            {
                "name": CONSUMER_PRODUCER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerproducerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
            },
        )

        consumer_producer_app.weave_from_topics(
            ToSection(
                topics={
                    TopicName("prev-output-topic"): TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                    TopicName("prev-error-topic"): TopicConfig(
                        type=OutputTopicTypes.ERROR, partitions_count=10
                    ),
                }
            )
        )

        assert consumer_producer_app.values.kafka.input_topics == [
            KafkaTopic(name="prev-output-topic"),
        ]

    async def test_deploy_order_when_dry_run_is_false(
        self, mocker: MockerFixture
    ) -> None:
        consumer_producer_app = ConsumerProducerApp.model_validate(
            {
                "name": CONSUMER_PRODUCER_APP_NAME,
                "namespace": NAMESPACE,
                "values": {
                    "image": "consumerproducerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "consumer-producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "consumer-producer-app-error-topic": TopicConfig(
                            type=OutputTopicTypes.ERROR, partitions_count=10
                        ),
                    }
                },
            },
        )
        mock_create_topic = mocker.patch.object(
            get_handlers().topic_handler, "create_topic"
        )
        mock_helm_upgrade_install = mocker.patch.object(
            consumer_producer_app._helm, "upgrade_install"
        )

        mock = mocker.AsyncMock()
        mock.attach_mock(mock_create_topic, "mock_create_topic")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")

        dry_run = False
        await consumer_producer_app.deploy(dry_run=dry_run)

        assert consumer_producer_app.to
        assert mock.mock_calls == [
            *(
                mocker.call.mock_create_topic(topic, dry_run=dry_run)
                for topic in consumer_producer_app.to.kafka_topics
            ),
            mocker.call.helm_upgrade_install(
                CONSUMER_PRODUCER_APP_RELEASE_NAME,
                "bakdata-streams-bootstrap/consumerproducer-app",
                dry_run,
                NAMESPACE,
                {
                    "nameOverride": CONSUMER_PRODUCER_APP_FULL_NAME,
                    "fullnameOverride": CONSUMER_PRODUCER_APP_FULL_NAME,
                    "image": "consumerproducerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                        "outputTopic": "consumer-producer-app-output-topic",
                        "errorTopic": "consumer-producer-app-error-topic",
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
        consumer_producer_app: ConsumerProducerApp,
        mocker: MockerFixture,
    ) -> None:
        mock_helm_uninstall = mocker.patch.object(
            consumer_producer_app._helm, "uninstall"
        )

        await consumer_producer_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            NAMESPACE, CONSUMER_PRODUCER_APP_RELEASE_NAME, True
        )

    async def test_reset_when_dry_run_is_false(
        self,
        consumer_producer_app: ConsumerProducerApp,
        mocker: MockerFixture,
    ) -> None:
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await consumer_producer_app.reset(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                NAMESPACE, CONSUMER_PRODUCER_APP_RELEASE_NAME, dry_run
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/consumerproducer-app-cleanup-job",
                dry_run,
                NAMESPACE,
                {
                    "nameOverride": CONSUMER_PRODUCER_APP_CLEAN_FULL_NAME,
                    "fullnameOverride": CONSUMER_PRODUCER_APP_CLEAN_FULL_NAME,
                    "image": "consumerproducerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                        "outputTopic": "consumer-producer-app-output-topic",
                        "deleteOutput": False,
                    },
                },
                HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    async def test_clean_when_dry_run_is_false(
        self,
        consumer_producer_app: ConsumerProducerApp,
        mocker: MockerFixture,
    ) -> None:
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await consumer_producer_app.clean(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                NAMESPACE, CONSUMER_PRODUCER_APP_RELEASE_NAME, dry_run
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/consumerproducer-app-cleanup-job",
                dry_run,
                NAMESPACE,
                {
                    "nameOverride": CONSUMER_PRODUCER_APP_CLEAN_FULL_NAME,
                    "fullnameOverride": CONSUMER_PRODUCER_APP_CLEAN_FULL_NAME,
                    "image": "consumerproducerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                        "outputTopic": "consumer-producer-app-output-topic",
                        "deleteOutput": True,
                    },
                },
                HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                NAMESPACE,
                CONSUMER_PRODUCER_APP_CLEAN_RELEASE_NAME,
                dry_run,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    async def test_get_input_output_topics(self) -> None:
        consumer_producer_app = ConsumerProducerApp.model_validate(
            {
                "name": "my-app",
                "namespace": NAMESPACE,
                "values": {
                    "image": "registry/consumerproducer-app",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "example-input": {"type": "input"},
                        "topic-extra": {"label": "role1"},
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

        assert consumer_producer_app.output_topic == KafkaTopic(name="example-output")
        assert consumer_producer_app.extra_output_topics == {
            "fake-role": KafkaTopic(name="extra-topic")
        }
        assert list(consumer_producer_app.outputs) == [
            KafkaTopic(name="example-output"),
            KafkaTopic(name="extra-topic"),
        ]
        assert list(consumer_producer_app.inputs) == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="topic-extra"),
        ]

    def test_raise_validation_error_when_persistence_enabled_and_size_not_set(
        self, stateful_consumer_producer_app: ConsumerProducerApp
    ) -> None:
        with pytest.raises(
            ValidationError,
            match=re.escape(
                "If app.persistence.enabled is set to true, the field app.persistence.size needs to be set."
            ),
        ):
            stateful_consumer_producer_app.values.persistence = PersistenceConfig(
                enabled=True
            )

    def test_generate(
        self, stateful_consumer_producer_app: ConsumerProducerApp
    ) -> None:
        assert stateful_consumer_producer_app.generate() == {
            "helm_name_override": CONSUMER_PRODUCER_APP_FULL_NAME,
            "helm_release_name": CONSUMER_PRODUCER_APP_RELEASE_NAME,
            "name": CONSUMER_PRODUCER_APP_NAME,
            "enabled": True,
            "namespace": NAMESPACE,
            "prefix": PREFIX,
            "to": {
                "models": {},
                "topics": {
                    "consumer-producer-app-output-topic": {
                        "configs": {},
                        "partitions_count": 10,
                        "type": "output",
                    }
                },
            },
            "type": "consumer-producer-app",
            "values": {
                "image": "consumerproducerApp",
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "outputTopic": "consumer-producer-app-output-topic",
                },
                "persistence": {"enabled": True, "size": "5Gi", "storageClass": "foo"},
                "statefulSet": True,
            },
            "version": "3.6.1",
        }

    @pytest.fixture()
    def mock_list_pvcs(self, mocker: MockerFixture) -> MagicMock:
        async def async_generator_side_effect() -> AsyncIterator[PersistentVolumeClaim]:
            for name in ("test-pvc1", "test-pvc2", "test-pvc3"):
                yield PersistentVolumeClaim(
                    apiVersion="v1",
                    kind="PersistentVolumeClaim",
                    metadata=ObjectMeta(name=name),
                    spec=PersistentVolumeClaimSpec(),
                    status=PersistentVolumeClaimStatus(),
                )

        return mocker.patch.object(
            PVCHandler, "list_pvcs", side_effect=async_generator_side_effect
        )

    @pytest.mark.usefixtures("kubeconfig")
    async def test_stateful_clean_deletes_pvcs(
        self,
        stateful_consumer_producer_app: ConsumerProducerApp,
        mock_list_pvcs: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(stateful_consumer_producer_app, "destroy")

        cleaner = stateful_consumer_producer_app._cleaner
        mocker.patch.object(cleaner, "destroy")
        mocker.patch.object(cleaner, "deploy")

        with capture_logs() as cap_logs:
            await stateful_consumer_producer_app.clean(dry_run=True)

        mock_list_pvcs.assert_called_once()
        assert {
            "event": "Deleting PVCs.",
            "app_name": CONSUMER_PRODUCER_APP_FULL_NAME,
            "namespace": NAMESPACE,
            "pvc_names": ["test-pvc1", "test-pvc2", "test-pvc3"],
            "log_level": "debug",
        } in cap_logs

    @pytest.mark.usefixtures("kubeconfig")
    async def test_stateless_clean_does_not_delete_pvcs(
        self,
        consumer_producer_app: ConsumerProducerApp,
        mock_list_pvcs: MagicMock,
        mocker: MockerFixture,
    ) -> None:
        mocker.patch.object(consumer_producer_app, "destroy")

        cleaner = consumer_producer_app._cleaner
        mocker.patch.object(cleaner, "destroy")
        mocker.patch.object(cleaner, "deploy")

        await consumer_producer_app.clean(dry_run=True)

        mock_list_pvcs.assert_not_called()
