import logging
from pathlib import Path
from unittest.mock import ANY, AsyncMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import HelmUpgradeInstallFlags
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components import ProducerApp
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap.producer.producer_app import ProducerAppCleaner
from kpops.config import KpopsConfig, TopicNameConfig

DEFAULTS_PATH = Path(__file__).parent / "resources"

PRODUCER_APP_NAME = "test-producer-app-with-long-name-0123456789abcdefghijklmnop"
PRODUCER_APP_FULL_NAME = "${pipeline.name}-" + PRODUCER_APP_NAME
PRODUCER_APP_RELEASE_NAME = create_helm_release_name(PRODUCER_APP_FULL_NAME)
PRODUCER_APP_CLEAN_FULL_NAME = PRODUCER_APP_FULL_NAME + "-clean"
PRODUCER_APP_CLEAN_RELEASE_NAME = create_helm_release_name(
    PRODUCER_APP_CLEAN_FULL_NAME, "-clean"
)


@pytest.mark.usefixtures("mock_env")
class TestProducerApp:
    def test_release_name(self):
        assert PRODUCER_APP_CLEAN_RELEASE_NAME.endswith("-clean")

    @pytest.fixture()
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=AsyncMock(),
            connector_handler=AsyncMock(),
            topic_handler=AsyncMock(),
        )

    @pytest.fixture()
    def config(self) -> KpopsConfig:
        return KpopsConfig(
            defaults_path=DEFAULTS_PATH,
            topic_name_config=TopicNameConfig(
                default_error_topic_name="${component.type}-error-topic",
                default_output_topic_name="${component.type}-output-topic",
            ),
        )

    @pytest.fixture()
    def producer_app(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ) -> ProducerApp:
        return ProducerApp(
            name=PRODUCER_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "version": "2.4.2",
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
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

    def test_cleaner(self, producer_app: ProducerApp):
        cleaner = producer_app._cleaner
        assert isinstance(cleaner, ProducerAppCleaner)
        assert not hasattr(cleaner, "_cleaner")

    def test_cleaner_inheritance(self, producer_app: ProducerApp):
        assert producer_app._cleaner.app == producer_app.app

    def test_cleaner_helm_release_name(self, producer_app: ProducerApp):
        assert (
            producer_app._cleaner.helm_release_name
            == "${pipeline.name}-test-producer-app-with-l-abc43-clean"
        )

    def test_cleaner_helm_name_override(self, producer_app: ProducerApp):
        assert (
            producer_app._cleaner.to_helm_values()["nameOverride"]
            == "${pipeline.name}-test-producer-app-with-long-name-0-abc43-clean"
        )

    def test_output_topics(self, config: KpopsConfig, handlers: ComponentHandlers):
        producer_app = ProducerApp(
            name=PRODUCER_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )

        assert producer_app.app.streams.output_topic == "producer-app-output-topic"
        assert producer_app.app.streams.extra_output_topics == {
            "first-extra-topic": "extra-topic-1"
        }

    @pytest.mark.asyncio()
    async def test_deploy_order_when_dry_run_is_false(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_create_topics = mocker.patch.object(
            producer_app.handlers.topic_handler, "create_topics"
        )

        mock_helm_upgrade_install = mocker.patch.object(
            producer_app.helm, "upgrade_install"
        )

        mock = mocker.AsyncMock()
        mock.attach_mock(mock_create_topics, "mock_create_topics")
        mock.attach_mock(mock_helm_upgrade_install, "mock_helm_upgrade_install")

        await producer_app.deploy(dry_run=False)
        assert mock.mock_calls == [
            mocker.call.mock_create_topics(to_section=producer_app.to, dry_run=False),
            mocker.call.mock_helm_upgrade_install(
                PRODUCER_APP_RELEASE_NAME,
                "bakdata-streams-bootstrap/producer-app",
                False,
                "test-namespace",
                {
                    "nameOverride": PRODUCER_APP_FULL_NAME,
                    "streams": {
                        "brokers": "fake-broker:9092",
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
                    version="2.4.2",
                    wait=True,
                    wait_for_jobs=False,
                ),
            ),
        ]

    @pytest.mark.asyncio()
    async def test_destroy(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_helm_uninstall = mocker.patch.object(producer_app.helm, "uninstall")

        await producer_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", PRODUCER_APP_RELEASE_NAME, True
        )

    @pytest.mark.asyncio()
    async def test_should_not_reset_producer_app(
        self,
        producer_app: ProducerApp,
        mocker: MockerFixture,
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            producer_app._cleaner.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(
            producer_app._cleaner.helm, "uninstall"
        )
        mock_helm_print_helm_diff = mocker.patch.object(
            producer_app._cleaner.dry_run_handler, "print_helm_diff"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")
        mock.attach_mock(mock_helm_print_helm_diff, "print_helm_diff")

        await producer_app.clean(dry_run=True)

        mock.assert_has_calls(
            [
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
                        "nameOverride": PRODUCER_APP_FULL_NAME,
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "producer-app-output-topic",
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.4.2", wait=True, wait_for_jobs=True
                    ),
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
        )

    @pytest.mark.asyncio()
    async def test_should_clean_producer_app_and_deploy_clean_up_job_and_delete_clean_up_with_dry_run_false(
        self, mocker: MockerFixture, producer_app: ProducerApp
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            producer_app._cleaner.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(
            producer_app._cleaner.helm, "uninstall"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        await producer_app.clean(dry_run=False)

        mock.assert_has_calls(
            [
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
                        "nameOverride": PRODUCER_APP_FULL_NAME,
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "producer-app-output-topic",
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.4.2", wait=True, wait_for_jobs=True
                    ),
                ),
                mocker.call.helm_uninstall(
                    "test-namespace",
                    PRODUCER_APP_CLEAN_RELEASE_NAME,
                    False,
                ),
                ANY,  # __bool__
                ANY,  # __str__
            ]
        )

    def test_get_output_topics(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
    ):
        producer_app = ProducerApp(
            name="my-producer",
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "producer-app-output-topic": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        assert producer_app.output_topic == "producer-app-output-topic"
        assert producer_app.extra_output_topics == {
            "first-extra-topic": "extra-topic-1"
        }
        assert producer_app.input_topics == []
        assert list(producer_app.inputs) == []
        assert list(producer_app.outputs) == [
            "producer-app-output-topic",
            "extra-topic-1",
        ]
