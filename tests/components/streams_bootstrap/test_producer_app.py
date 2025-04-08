import logging
from unittest.mock import ANY, MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import get_handlers
from kpops.component_handlers.helm_wrapper.dry_run_handler import DryRunHandler
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmUpgradeInstallFlags
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.common.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap.producer.producer_app import (
    ProducerApp,
    ProducerAppCleaner,
)
from kpops.core.exception import ValidationError

PRODUCER_APP_NAME = "test-producer-app-with-long-name-0123456789abcdefghijklmnop"
PRODUCER_APP_FULL_NAME = "${pipeline.name}-" + PRODUCER_APP_NAME
PRODUCER_APP_HELM_NAME_OVERRIDE = (
    "${pipeline.name}-" + "test-producer-app-with-long-name-0123456-c4c51"
)
PRODUCER_APP_RELEASE_NAME = create_helm_release_name(PRODUCER_APP_FULL_NAME)
PRODUCER_APP_CLEAN_FULL_NAME = PRODUCER_APP_FULL_NAME + "-clean"
PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE = (
    "${pipeline.name}-" + "test-producer-app-with-long-name-0-abc43-clean"
)
PRODUCER_APP_CLEAN_RELEASE_NAME = create_helm_release_name(
    PRODUCER_APP_CLEAN_FULL_NAME, "-clean"
)


@pytest.mark.usefixtures("mock_env")
class TestProducerApp:
    def test_release_name(self):
        assert PRODUCER_APP_CLEAN_RELEASE_NAME.endswith("-clean")

    @pytest.fixture()
    def producer_app(self) -> ProducerApp:
        producer = ProducerApp.model_validate(
            {
                "name": PRODUCER_APP_NAME,
                "version": "3.2.1",
                "namespace": "test-namespace",
                "values": {
                    "image": "ProducerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "clean_schemas": True,
                "to": {
                    "topics": {
                        "producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )
        assert producer.is_cron_job is False
        return producer

    @pytest.fixture()
    def producer_app_cron_job(self) -> ProducerApp:
        producer = ProducerApp.model_validate(
            {
                "name": PRODUCER_APP_NAME,
                "version": "3.2.1",
                "namespace": "test-namespace",
                "values": {
                    "image": "ProducerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                    "schedule": "0 12 * * *",
                },
                "clean_schemas": True,
                "to": {
                    "topics": {
                        "producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )
        assert producer.is_cron_job is True
        return producer

    @pytest.fixture(autouse=True)
    def empty_helm_get_values(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "get_values", return_value=None)

    def test_helm_name_override(self, producer_app: ProducerApp):
        assert len(producer_app.helm_name_override) == 63
        assert producer_app.helm_name_override == PRODUCER_APP_HELM_NAME_OVERRIDE

    def test_cron_job_helm_name_override(self, producer_app_cron_job: ProducerApp):
        assert len(producer_app_cron_job.helm_name_override) == 52
        assert (
            producer_app_cron_job.helm_name_override
            == "${pipeline.name}-test-producer-app-with-long-n-c4c51"
        )

    def test_cleaner(self, producer_app: ProducerApp):
        cleaner = producer_app._cleaner
        assert isinstance(cleaner, ProducerAppCleaner)
        assert not hasattr(cleaner, "_cleaner")

    def test_cleaner_inheritance(self, producer_app: ProducerApp):
        assert producer_app._cleaner.values == producer_app.values

    def test_cleaner_helm_release_name(self, producer_app: ProducerApp):
        assert (
            producer_app._cleaner.helm_release_name
            == "${pipeline.name}-test-producer-app-with-l-abc43-clean"
        )

    def test_cleaner_helm_name_override(self, producer_app: ProducerApp):
        assert (
            producer_app._cleaner.to_helm_values()["nameOverride"]
            == PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE
        )
        assert (
            producer_app._cleaner.to_helm_values()["fullnameOverride"]
            == PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE
        )

    def test_output_topics(self):
        producer_app = ProducerApp.model_validate(
            {
                "name": PRODUCER_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "namespace": "test-namespace",
                    "image": "ProducerApp",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            label="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )

        assert producer_app.values.kafka.output_topic == KafkaTopic(
            name="producer-app-output-topic"
        )
        assert producer_app.values.kafka.labeled_output_topics == {
            "first-extra-topic": KafkaTopic(name="extra-topic-1")
        }

    async def test_deploy_order_when_dry_run_is_false(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock = mocker.AsyncMock()
        mock_create_topic = mocker.patch.object(
            get_handlers().topic_handler, "create_topic"
        )
        mock.attach_mock(mock_create_topic, "mock_create_topic")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "mock_helm_upgrade_install")

        await producer_app.deploy(dry_run=False)
        assert producer_app.to
        assert mock.mock_calls == [
            *(
                mocker.call.mock_create_topic(topic, dry_run=False)
                for topic in producer_app.to.kafka_topics
            ),
            mocker.call.mock_helm_upgrade_install(
                PRODUCER_APP_RELEASE_NAME,
                "bakdata-streams-bootstrap/producer-app",
                False,
                "test-namespace",
                {
                    "nameOverride": PRODUCER_APP_HELM_NAME_OVERRIDE,
                    "fullnameOverride": PRODUCER_APP_HELM_NAME_OVERRIDE,
                    "image": "ProducerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                        "outputTopic": "producer-app-output-topic",
                    },
                },
                HelmUpgradeInstallFlags(
                    force=False,
                    username=None,
                    password=None,
                    ca_file=None,
                    insecure_skip_tls_verify=False,
                    timeout="5m0s",
                    version="3.2.1",
                    wait=True,
                    wait_for_jobs=False,
                ),
            ),
        ]

    async def test_destroy(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")

        await producer_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", PRODUCER_APP_RELEASE_NAME, True
        )

    async def test_should_clean_producer_app(
        self,
        producer_app: ProducerApp,
        empty_helm_get_values: MockerFixture,
        mocker: MockerFixture,
    ):
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")
        mock_helm_print_helm_diff = mocker.patch.object(
            DryRunHandler, "print_helm_diff"
        )
        mock.attach_mock(mock_helm_print_helm_diff, "print_helm_diff")

        await producer_app.clean(dry_run=True)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace", PRODUCER_APP_RELEASE_NAME, True
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                "test-namespace",
                PRODUCER_APP_CLEAN_RELEASE_NAME,
                True,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                PRODUCER_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/producer-app-cleanup-job",
                True,
                "test-namespace",
                {
                    "nameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                    "fullnameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                    "image": "ProducerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                        "outputTopic": "producer-app-output-topic",
                    },
                },
                HelmUpgradeInstallFlags(version="3.2.1", wait=True, wait_for_jobs=True),
            ),
            mocker.call.print_helm_diff(
                ANY,
                PRODUCER_APP_CLEAN_RELEASE_NAME,
                logging.getLogger("HelmApp"),
            ),
            mocker.call.helm_uninstall(
                "test-namespace",
                PRODUCER_APP_CLEAN_RELEASE_NAME,
                True,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    async def test_should_clean_producer_app_and_deploy_clean_up_job_and_delete_clean_up_with_dry_run_false(
        self,
        mocker: MockerFixture,
        producer_app: ProducerApp,
        empty_helm_get_values: MockerFixture,
    ):
        mock = mocker.MagicMock()
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        await producer_app.clean(dry_run=False)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace", PRODUCER_APP_RELEASE_NAME, False
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_uninstall(
                "test-namespace",
                PRODUCER_APP_CLEAN_RELEASE_NAME,
                False,
            ),
            ANY,  # __bool__
            ANY,  # __str__
            mocker.call.helm_upgrade_install(
                PRODUCER_APP_CLEAN_RELEASE_NAME,
                "bakdata-streams-bootstrap/producer-app-cleanup-job",
                False,
                "test-namespace",
                {
                    "nameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                    "fullnameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                    "image": "ProducerApp",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                        "outputTopic": "producer-app-output-topic",
                    },
                },
                HelmUpgradeInstallFlags(version="3.2.1", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                "test-namespace",
                PRODUCER_APP_CLEAN_RELEASE_NAME,
                False,
            ),
            ANY,  # __bool__
            ANY,  # __str__
        ]

    def test_get_output_topics(self):
        producer_app = ProducerApp.model_validate(
            {
                "name": "my-producer",
                "namespace": "test-namespace",
                "values": {
                    "image": "producer-app",
                    "namespace": "test-namespace",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            label="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        assert producer_app.values.kafka.output_topic == KafkaTopic(
            name="producer-app-output-topic"
        )
        assert producer_app.values.kafka.labeled_output_topics == {
            "first-extra-topic": KafkaTopic(name="extra-topic-1")
        }
        assert producer_app.input_topics == []
        assert list(producer_app.inputs) == []
        assert list(producer_app.outputs) == [
            KafkaTopic(name="producer-app-output-topic"),
            KafkaTopic(name="extra-topic-1"),
        ]

    async def test_should_not_deploy_clean_up_when_rest(self, mocker: MockerFixture):
        image_tag_in_cluster = "1.1.1"
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/producer-app",
                "imageTag": image_tag_in_cluster,
                "nameOverride": PRODUCER_APP_NAME,
                "fullnameOverride": PRODUCER_APP_NAME,
                "replicaCount": 1,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "outputTopic": "test-output-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )
        producer_app = ProducerApp.model_validate(
            {
                "name": PRODUCER_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "image": "registry/producer-app",
                    "imageTag": "2.2.2",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "test-output-topic": {"type": "output"},
                    }
                },
            },
        )
        mock_helm_uninstall = mocker.patch.object(Helm, "uninstall")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mocker.patch.object(DryRunHandler, "print_helm_diff")

        dry_run = True
        await producer_app.reset(dry_run)
        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", PRODUCER_APP_RELEASE_NAME, dry_run
        )
        mock_helm_upgrade_install.assert_not_called()

    async def test_should_deploy_clean_up_job_with_values_in_cluster_when_clean(
        self, mocker: MockerFixture
    ):
        image_tag_in_cluster = "1.1.1"
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/producer-app",
                "imageTag": image_tag_in_cluster,
                "nameOverride": PRODUCER_APP_NAME,
                "fullnameOverride": PRODUCER_APP_NAME,
                "replicaCount": 1,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "outputTopic": "test-output-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )
        producer_app = ProducerApp.model_validate(
            {
                "name": PRODUCER_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "image": "registry/producer-app",
                    "imageTag": "2.2.2",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "test-output-topic": {"type": "output"},
                    }
                },
            },
        )
        mocker.patch.object(Helm, "uninstall")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mocker.patch.object(DryRunHandler, "print_helm_diff")

        dry_run = True
        await producer_app.clean(dry_run)

        mock_helm_upgrade_install.assert_called_once_with(
            PRODUCER_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/producer-app-cleanup-job",
            dry_run,
            "test-namespace",
            {
                "image": "registry/producer-app",
                "nameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                "fullnameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                "imageTag": image_tag_in_cluster,
                "replicaCount": 1,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "outputTopic": "test-output-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
            HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
        )

    async def test_clean_should_fall_back_to_local_values_when_validation_of_cluster_values_fails(
        self, mocker: MockerFixture, caplog: pytest.LogCaptureFixture
    ):
        caplog.set_level(logging.WARNING)

        # invalid model
        mocker.patch.object(
            Helm,
            "get_values",
            return_value={
                "image": "registry/producer-app",
                "imageTag": "1.1.1",
                "nameOverride": PRODUCER_APP_NAME,
                "fullnameOverride": PRODUCER_APP_NAME,
                "streams": {
                    "brokers": "fake-broker:9092",
                    "outputTopic": "test-output-topic",
                    "schemaRegistryUrl": "http://localhost:8081",
                },
            },
        )

        # user defined model
        producer_app = ProducerApp.model_validate(
            {
                "name": PRODUCER_APP_NAME,
                "namespace": "test-namespace",
                "values": {
                    "image": "registry/producer-app",
                    "imageTag": "2.2.2",
                    "kafka": {"bootstrapServers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "test-output-topic": {"type": "output"},
                    }
                },
            },
        )
        mocker.patch.object(Helm, "uninstall")
        mock_helm_upgrade_install = mocker.patch.object(Helm, "upgrade_install")
        mocker.patch.object(DryRunHandler, "print_helm_diff")

        dry_run = True
        await producer_app.clean(dry_run)
        assert (
            "The values in the cluster are invalid with the current model. Falling back to the enriched values of pipeline.yaml and defaults.yaml"
            in caplog.text
        )

        mock_helm_upgrade_install.assert_called_once_with(
            PRODUCER_APP_CLEAN_RELEASE_NAME,
            "bakdata-streams-bootstrap/producer-app-cleanup-job",
            dry_run,
            "test-namespace",
            {
                "image": "registry/producer-app",
                "imageTag": "2.2.2",
                "nameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                "fullnameOverride": PRODUCER_APP_CLEAN_HELM_NAMEOVERRIDE,
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "outputTopic": "test-output-topic",
                },
            },
            HelmUpgradeInstallFlags(version="3.6.1", wait=True, wait_for_jobs=True),
        )

    def test_validate_cron_expression(self):
        with pytest.raises(ValidationError):
            assert ProducerApp.model_validate(
                {
                    "name": PRODUCER_APP_NAME,
                    "namespace": "test-namespace",
                    "values": {
                        "image": "registry/producer-app",
                        "imageTag": "2.2.2",
                        "kafka": {"bootstrapServers": "fake-broker:9092"},
                        "schedule": "0 wrong_value 1 * *",  # Invalid Cron Expression
                    },
                    "to": {
                        "topics": {
                            "test-output-topic": {"type": "output"},
                        }
                    },
                },
            )
