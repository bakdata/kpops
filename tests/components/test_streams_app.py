import logging
from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components import StreamsApp
from kpops.components.base_components.models import TopicName
from kpops.components.base_components.models.to_section import (
    ToSection,
)
from kpops.components.base_components.models.topic import (
    KafkaTopic,
    OutputTopicTypes,
    TopicConfig,
)
from kpops.components.streams_bootstrap.streams.model import (
    PersistenceConfig,
    StreamsAppAutoScaling,
)
from kpops.components.streams_bootstrap.streams.streams_app import (
    StreamsAppCleaner,
)
from kpops.config import KpopsConfig, TopicNameConfig
from kpops.pipeline import ValidationError
from tests.components import PIPELINE_BASE_DIR

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


@pytest.mark.usefixtures("mock_env")
class TestStreamsApp:
    def test_release_name(self):
        assert STREAMS_APP_CLEAN_RELEASE_NAME.endswith("-clean")

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
            topic_name_config=TopicNameConfig(
                default_error_topic_name="${component.type}-error-topic",
                default_output_topic_name="${component.type}-output-topic",
            ),
            helm_diff_config=HelmDiffConfig(),
            pipeline_base_dir=PIPELINE_BASE_DIR,
        )

    @pytest.fixture()
    def streams_app(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ) -> StreamsApp:
        return StreamsApp(
            name=STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
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
    def stateful_streams_app(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ) -> StreamsApp:
        return StreamsApp(
            name=STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
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

    @pytest.fixture()
    def dry_run_handler_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.DryRunHandler"
        ).return_value

    def test_cleaner(self, streams_app: StreamsApp):
        cleaner = streams_app._cleaner
        assert isinstance(cleaner, StreamsAppCleaner)
        assert not hasattr(cleaner, "_cleaner")

    def test_cleaner_inheritance(self, streams_app: StreamsApp):
        streams_app.app.autoscaling = StreamsAppAutoScaling(
            enabled=True,
            consumer_group="foo",
            lag_threshold=100,
            idle_replicas=1,
        )
        assert streams_app._cleaner.app == streams_app.app

    def test_raise_validation_error_when_autoscaling_enabled_and_mandatory_fields_not_set(
        self, streams_app: StreamsApp
    ):
        with pytest.raises(ValidationError) as error:
            streams_app.app.autoscaling = StreamsAppAutoScaling(
                enabled=True,
            )
        msg = (
            "If app.autoscaling.enabled is set to true, "
            "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
        )
        assert str(error.value) == msg

    def test_raise_validation_error_when_autoscaling_enabled_and_only_consumer_group_set(
        self, streams_app: StreamsApp
    ):
        with pytest.raises(ValidationError) as error:
            streams_app.app.autoscaling = StreamsAppAutoScaling(
                enabled=True, consumer_group="a-test-group"
            )
        msg = (
            "If app.autoscaling.enabled is set to true, "
            "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
        )
        assert str(error.value) == msg

    def test_raise_validation_error_when_autoscaling_enabled_and_only_lag_threshold_is_set(
        self, streams_app: StreamsApp
    ):
        with pytest.raises(ValidationError) as error:
            streams_app.app.autoscaling = StreamsAppAutoScaling(
                enabled=True, lag_threshold=1000
            )
        msg = (
            "If app.autoscaling.enabled is set to true, "
            "the fields app.autoscaling.consumer_group and app.autoscaling.lag_threshold should be set."
        )
        assert str(error.value) == msg

    def test_cleaner_helm_release_name(self, streams_app: StreamsApp):
        assert (
            streams_app._cleaner.helm_release_name
            == "${pipeline.name}-test-streams-app-with-lo-c98c5-clean"
        )

    def test_cleaner_helm_name_override(self, streams_app: StreamsApp):
        assert (
            streams_app._cleaner.to_helm_values()["nameOverride"]
            == STREAMS_APP_CLEAN_HELM_NAME_OVERRIDE
        )

    def test_set_topics(self, config: KpopsConfig, handlers: ComponentHandlers):
        streams_app = StreamsApp(
            name=STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "example-input": {"type": "input"},
                        "b": {"type": "input"},
                        "a": {"type": "input"},
                        "topic-extra2": {"role": "role2"},
                        "topic-extra3": {"role": "role2"},
                        "topic-extra": {"role": "role1"},
                        ".*": {"type": "pattern"},
                        "example.*": {
                            "type": "pattern",
                            "role": "another-pattern",
                        },
                    }
                },
            },
        )
        assert streams_app.app.streams.input_topics == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]
        assert streams_app.app.streams.extra_input_topics == {
            "role1": [KafkaTopic(name="topic-extra")],
            "role2": [KafkaTopic(name="topic-extra2"), KafkaTopic(name="topic-extra3")],
        }
        assert streams_app.app.streams.input_pattern == ".*"
        assert streams_app.app.streams.extra_input_patterns == {
            "another-pattern": "example.*"
        }

        helm_values = streams_app.to_helm_values()
        streams_config = helm_values["streams"]
        assert streams_config["inputTopics"]
        assert "extraInputTopics" in streams_config
        assert "inputPattern" in streams_config
        assert "extraInputPatterns" in streams_config

    def test_no_empty_input_topic(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name=STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        ".*": {"type": "pattern"},
                    }
                },
            },
        )
        assert not streams_app.app.streams.extra_input_topics
        assert not streams_app.app.streams.input_topics
        assert streams_app.app.streams.input_pattern == ".*"
        assert not streams_app.app.streams.extra_input_patterns

        helm_values = streams_app.to_helm_values()
        streams_config = helm_values["streams"]
        assert "inputTopics" not in streams_config
        assert "extraInputTopics" not in streams_config
        assert "inputPattern" in streams_config
        assert "extraInputPatterns" not in streams_config

    def test_should_validate(self, config: KpopsConfig, handlers: ComponentHandlers):
        # An exception should be raised when both role and type are defined and type is input
        with pytest.raises(
            ValueError, match="Define role only if `type` is `pattern` or `None`"
        ):
            StreamsApp(
                name=STREAMS_APP_NAME,
                config=config,
                handlers=handlers,
                **{
                    "namespace": "test-namespace",
                    "app": {
                        "streams": {"brokers": "fake-broker:9092"},
                    },
                    "from": {
                        "topics": {
                            "topic-input": {
                                "type": "input",
                                "role": "role",
                            }
                        }
                    },
                },
            )

        # An exception should be raised when both role and type are defined and type is error
        with pytest.raises(
            ValueError, match="Define `role` only if `type` is undefined"
        ):
            StreamsApp(
                name=STREAMS_APP_NAME,
                config=config,
                handlers=handlers,
                **{
                    "namespace": "test-namespace",
                    "app": {
                        "streams": {"brokers": "fake-broker:9092"},
                    },
                    "to": {
                        "topics": {
                            "topic-input": {
                                "type": "error",
                                "role": "role",
                            }
                        }
                    },
                },
            )

    def test_set_streams_output_from_to(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name=STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
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
                            role="first-extra-role",
                            partitions_count=10,
                        ),
                        "extra-topic-2": TopicConfig(
                            role="second-extra-role",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        assert streams_app.app.streams.extra_output_topics == {
            "first-extra-role": KafkaTopic(name="extra-topic-1"),
            "second-extra-role": KafkaTopic(name="extra-topic-2"),
        }
        assert streams_app.app.streams.output_topic == KafkaTopic(
            name="streams-app-output-topic"
        )
        assert streams_app.app.streams.error_topic == KafkaTopic(
            name="streams-app-error-topic"
        )

    def test_weave_inputs_from_prev_component(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name=STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
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

        assert streams_app.app.streams.input_topics == [
            KafkaTopic(name="prev-output-topic"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]

    @pytest.mark.asyncio()
    async def test_deploy_order_when_dry_run_is_false(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        streams_app = StreamsApp(
            name=STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
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
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                        "extra-topic-2": TopicConfig(
                            role="second-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        mock_create_topic = mocker.patch.object(
            streams_app.handlers.topic_handler, "create_topic"
        )
        mock_helm_upgrade_install = mocker.patch.object(
            streams_app.helm, "upgrade_install"
        )

        mock = mocker.AsyncMock()
        mock.attach_mock(mock_create_topic, "mock_create_topic")
        mock.attach_mock(mock_helm_upgrade_install, "mock_helm_upgrade_install")

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
                    role="first-extra-topic",
                ),
            ),
            KafkaTopic(
                name="extra-topic-2",
                config=TopicConfig(
                    partitions_count=10,
                    role="second-extra-topic",
                ),
            ),
        ]
        assert mock.mock_calls == [
            *(
                mocker.call.mock_create_topic(topic, dry_run=dry_run)
                for topic in streams_app.to.kafka_topics
            ),
            mocker.call.mock_helm_upgrade_install(
                STREAMS_APP_RELEASE_NAME,
                "bakdata-streams-bootstrap/streams-app",
                dry_run,
                "test-namespace",
                {
                    "nameOverride": STREAMS_APP_HELM_NAME_OVERRIDE,
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

    @pytest.mark.asyncio()
    async def test_destroy(self, streams_app: StreamsApp, mocker: MockerFixture):
        mock_helm_uninstall = mocker.patch.object(streams_app.helm, "uninstall")

        await streams_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", STREAMS_APP_RELEASE_NAME, True
        )

    @pytest.mark.asyncio()
    async def test_reset_when_dry_run_is_false(
        self, streams_app: StreamsApp, mocker: MockerFixture
    ):
        cleaner = streams_app._cleaner
        assert isinstance(cleaner, StreamsAppCleaner)

        mock_helm_upgrade_install = mocker.patch.object(cleaner.helm, "upgrade_install")
        mock_helm_uninstall = mocker.patch.object(cleaner.helm, "uninstall")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await streams_app.reset(dry_run=dry_run)

        mock.assert_has_calls(
            [
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
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "streams-app-output-topic",
                            "deleteOutput": False,
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.9.0", wait=True, wait_for_jobs=True
                    ),
                ),
                mocker.call.helm_uninstall(
                    "test-namespace",
                    STREAMS_APP_CLEAN_RELEASE_NAME,
                    dry_run,
                ),
            ]
        )

    @pytest.mark.asyncio()
    async def test_should_clean_streams_app_and_deploy_clean_up_job_and_delete_clean_up(
        self,
        streams_app: StreamsApp,
        mocker: MockerFixture,
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            streams_app._cleaner.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(
            streams_app._cleaner.helm, "uninstall"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await streams_app.clean(dry_run=dry_run)

        mock.assert_has_calls(
            [
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
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "streams-app-output-topic",
                            "deleteOutput": True,
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.9.0", wait=True, wait_for_jobs=True
                    ),
                ),
                mocker.call.helm_uninstall(
                    "test-namespace",
                    STREAMS_APP_CLEAN_RELEASE_NAME,
                    dry_run,
                ),
            ]
        )

    @pytest.mark.asyncio()
    async def test_get_input_output_topics(
        self, config: KpopsConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name="my-app",
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        "example-input": {"type": "input"},
                        "b": {"type": "input"},
                        "a": {"type": "input"},
                        "topic-extra2": {"role": "role2"},
                        "topic-extra3": {"role": "role2"},
                        "topic-extra": {"role": "role1"},
                        ".*": {"type": "pattern"},
                        "example.*": {
                            "type": "pattern",
                            "role": "another-pattern",
                        },
                    }
                },
                "to": {
                    "topics": {
                        "example-output": {"type": "output"},
                        "extra-topic": {"role": "fake-role"},
                    }
                },
            },
        )

        assert streams_app.app.streams.input_topics == [
            KafkaTopic(name="example-input"),
            KafkaTopic(name="b"),
            KafkaTopic(name="a"),
        ]
        assert streams_app.app.streams.extra_input_topics == {
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
        self, stateful_streams_app: StreamsApp
    ):
        with pytest.raises(ValidationError) as error:
            stateful_streams_app.app.persistence = PersistenceConfig(
                enabled=True,
            )
        msg = (
            "If app.persistence.enabled is set to true, "
            "the field app.persistence.size needs to be set."
        )
        assert str(error.value) == msg

    @pytest.mark.asyncio()
    async def test_stateful_clean_with_dry_run_false(
        self, stateful_streams_app: StreamsApp, mocker: MockerFixture
    ):
        cleaner = stateful_streams_app._cleaner
        assert isinstance(cleaner, StreamsAppCleaner)

        mock_helm_upgrade_install = mocker.patch.object(cleaner.helm, "upgrade_install")
        mock_helm_uninstall = mocker.patch.object(cleaner.helm, "uninstall")
        mock_delete_pvcs = mocker.patch.object(cleaner.pvc_handler, "delete_pvcs")

        mock = MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")
        mock.attach_mock(mock_delete_pvcs, "delete_pvcs")

        dry_run = False
        await stateful_streams_app.clean(dry_run=dry_run)

        mock.assert_has_calls(
            [
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
                        "statefulSet": True,
                        "persistence": {"enabled": True, "size": "5Gi"},
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "streams-app-output-topic",
                            "deleteOutput": True,
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.9.0", wait=True, wait_for_jobs=True
                    ),
                ),
                mocker.call.helm_uninstall(
                    "test-namespace",
                    STREAMS_APP_CLEAN_RELEASE_NAME,
                    dry_run,
                ),
                ANY,  # __bool__
                ANY,  # __str__
                mocker.call.delete_pvcs(),
            ]
        )

    @pytest.mark.asyncio()
    async def test_stateful_clean_with_dry_run_true(
        self,
        stateful_streams_app: StreamsApp,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
    ):
        caplog.set_level(logging.INFO)
        cleaner = stateful_streams_app._cleaner
        assert isinstance(cleaner, StreamsAppCleaner)

        pvc_names = ["test-pvc1", "test-pvc2", "test-pvc3"]

        mocker.patch.object(cleaner, "destroy")
        mocker.patch.object(cleaner, "deploy")
        mock_get_pvc_names = mocker.patch.object(cleaner.pvc_handler, "get_pvc_names")
        mock_get_pvc_names.return_value = pvc_names

        dry_run = True
        await stateful_streams_app.clean(dry_run=dry_run)
        mock_get_pvc_names.assert_called_once()
        assert (
            f"Deleting the PVCs {pvc_names} for StatefulSet '{STREAMS_APP_CLEAN_FULL_NAME}'"
            in caplog.text
        )
