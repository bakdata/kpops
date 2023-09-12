from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig, TopicNameConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmUpgradeInstallFlags,
)
from kpops.components import StreamsApp
from kpops.components.base_components.models import TopicName
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestStreamsApp:
    STREAMS_APP_NAME = "test-streams-app-with-long-name-0123456789abcdefghijklmnop"
    STREAMS_APP_CLEAN_NAME = "test-streams-app-with-long-name-0123456789abcd-clean"

    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=AsyncMock(),
            connector_handler=AsyncMock(),
            topic_handler=AsyncMock(),
        )

    @pytest.fixture
    def config(self) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            topic_name_config=TopicNameConfig(
                default_error_topic_name="${component_type}-error-topic",
                default_output_topic_name="${component_type}-output-topic",
            ),
            helm_diff_config=HelmDiffConfig(),
        )

    @pytest.fixture
    def streams_app(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ) -> StreamsApp:
        return StreamsApp(
            name=self.STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${output_topic_name}": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                    }
                },
            },
        )

    def test_set_topics(self, config: PipelineConfig, handlers: ComponentHandlers):
        streams_app = StreamsApp(
            name=self.STREAMS_APP_NAME,
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
                        "topic-extra2": {"type": "extra", "role": "role2"},
                        "topic-extra3": {"type": "extra", "role": "role2"},
                        "topic-extra": {"type": "extra", "role": "role1"},
                        ".*": {"type": "input-pattern"},
                        "example.*": {
                            "type": "extra-pattern",
                            "role": "another-pattern",
                        },
                    }
                },
            },
        )
        assert streams_app.app.streams.extra_input_topics == {
            "role1": ["topic-extra"],
            "role2": ["topic-extra2", "topic-extra3"],
        }
        assert streams_app.app.streams.input_topics == ["example-input", "b", "a"]
        assert streams_app.app.streams.input_pattern == ".*"
        assert streams_app.app.streams.extra_input_patterns == {
            "another-pattern": "example.*"
        }

        helm_values = streams_app.to_helm_values()
        streams_config = helm_values["streams"]
        assert "inputTopics" in streams_config
        assert "extraInputTopics" in streams_config
        assert "inputPattern" in streams_config
        assert "extraInputPatterns" in streams_config

    def test_no_empty_input_topic(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name=self.STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "from": {
                    "topics": {
                        ".*": {"type": "input-pattern"},
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

    def test_should_validate(self, config: PipelineConfig, handlers: ComponentHandlers):
        with pytest.raises(ValueError):
            StreamsApp(
                name=self.STREAMS_APP_NAME,
                config=config,
                handlers=handlers,
                **{
                    "namespace": "test-namespace",
                    "app": {
                        "streams": {"brokers": "fake-broker:9092"},
                    },
                    "from": {
                        "topics": {
                            "topic-extra": {
                                "type": "extra",
                            }
                        }
                    },
                },
            )

        with pytest.raises(ValueError):
            StreamsApp(
                name=self.STREAMS_APP_NAME,
                config=config,
                handlers=handlers,
                **{
                    "namespace": "test-namespace",
                    "app": {
                        "streams": {"brokers": "fake-broker:9092"},
                    },
                    "from": {"topics": {"example.*": {"type": "extra-pattern"}}},
                },
            )

    def test_set_streams_output_from_to(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name=self.STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${output_topic_name}": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "${error_topic_name}": TopicConfig(
                            type=OutputTopicTypes.ERROR, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            type=OutputTopicTypes.EXTRA,
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                        "extra-topic-2": TopicConfig(
                            type=OutputTopicTypes.EXTRA,
                            role="second-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        assert streams_app.app.streams.extra_output_topics == {
            "first-extra-topic": "extra-topic-1",
            "second-extra-topic": "extra-topic-2",
        }
        assert streams_app.app.streams.output_topic == "${output_topic_name}"
        assert streams_app.app.streams.error_topic == "${error_topic_name}"

    def test_weave_inputs_from_prev_component(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name=self.STREAMS_APP_NAME,
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

        assert streams_app.app.streams.input_topics == ["prev-output-topic", "b", "a"]

    @pytest.mark.asyncio
    async def test_deploy_order_when_dry_run_is_false(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        streams_app = StreamsApp(
            name=self.STREAMS_APP_NAME,
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${output_topic_name}": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "${error_topic_name}": TopicConfig(
                            type=OutputTopicTypes.ERROR, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            type=OutputTopicTypes.EXTRA,
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                        "extra-topic-2": TopicConfig(
                            type=OutputTopicTypes.EXTRA,
                            role="second-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        mock_create_topics = mocker.patch.object(
            streams_app.handlers.topic_handler, "create_topics"
        )
        mock_helm_upgrade_install = mocker.patch.object(
            streams_app.helm, "upgrade_install"
        )

        mock = mocker.AsyncMock()
        mock.attach_mock(mock_create_topics, "mock_create_topics")
        mock.attach_mock(mock_helm_upgrade_install, "mock_helm_upgrade_install")

        dry_run = False
        await streams_app.deploy(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.mock_create_topics(to_section=streams_app.to, dry_run=dry_run),
            mocker.call.mock_helm_upgrade_install(
                self.STREAMS_APP_NAME,
                "bakdata-streams-bootstrap/streams-app",
                dry_run,
                "test-namespace",
                {
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "extraOutputTopics": {
                            "first-extra-topic": "extra-topic-1",
                            "second-extra-topic": "extra-topic-2",
                        },
                        "outputTopic": "${output_topic_name}",
                        "errorTopic": "${error_topic_name}",
                    }
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

    @pytest.mark.asyncio
    async def test_destroy(self, streams_app: StreamsApp, mocker: MockerFixture):
        mock_helm_uninstall = mocker.patch.object(streams_app.helm, "uninstall")

        await streams_app.destroy(dry_run=True)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", self.STREAMS_APP_NAME, True
        )

    @pytest.mark.asyncio
    async def test_reset_when_dry_run_is_false(
        self, streams_app: StreamsApp, mocker: MockerFixture
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            streams_app.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(streams_app.helm, "uninstall")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await streams_app.reset(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace", self.STREAMS_APP_CLEAN_NAME, dry_run
            ),
            mocker.call.helm_upgrade_install(
                self.STREAMS_APP_CLEAN_NAME,
                "bakdata-streams-bootstrap/streams-app-cleanup-job",
                dry_run,
                "test-namespace",
                {
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "${output_topic_name}",
                        "deleteOutput": False,
                    },
                },
                HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                "test-namespace", self.STREAMS_APP_CLEAN_NAME, dry_run
            ),
        ]

    @pytest.mark.asyncio
    async def test_should_clean_streams_app_and_deploy_clean_up_job_and_delete_clean_up(
        self,
        streams_app: StreamsApp,
        mocker: MockerFixture,
    ):
        mock_helm_upgrade_install = mocker.patch.object(
            streams_app.helm, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(streams_app.helm, "uninstall")

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")

        dry_run = False
        await streams_app.clean(dry_run=dry_run)

        assert mock.mock_calls == [
            mocker.call.helm_uninstall(
                "test-namespace", self.STREAMS_APP_CLEAN_NAME, dry_run
            ),
            mocker.call.helm_upgrade_install(
                self.STREAMS_APP_CLEAN_NAME,
                "bakdata-streams-bootstrap/streams-app-cleanup-job",
                dry_run,
                "test-namespace",
                {
                    "streams": {
                        "brokers": "fake-broker:9092",
                        "outputTopic": "${output_topic_name}",
                        "deleteOutput": True,
                    },
                },
                HelmUpgradeInstallFlags(version="2.9.0", wait=True, wait_for_jobs=True),
            ),
            mocker.call.helm_uninstall(
                "test-namespace", self.STREAMS_APP_CLEAN_NAME, dry_run
            ),
        ]

    @pytest.mark.asyncio
    async def test_get_input_output_topics(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            name=self.STREAMS_APP_NAME,
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
                        "topic-extra2": {"type": "extra", "role": "role2"},
                        "topic-extra3": {"type": "extra", "role": "role2"},
                        "topic-extra": {"type": "extra", "role": "role1"},
                        ".*": {"type": "input-pattern"},
                        "example.*": {
                            "type": "extra-pattern",
                            "role": "another-pattern",
                        },
                    }
                },
                "to": {"topics": {"example-output": {"type": "output"}}},
            },
        )
        assert streams_app.get_input_topics() == ["example-input", "b", "a"]
        assert streams_app.get_extra_input_topics() == {
            "role1": ["topic-extra"],
            "role2": ["topic-extra2", "topic-extra3"],
        }
        assert streams_app.get_output_topic() == "example-output"
