from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig, TopicNameConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.components import StreamsApp
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestStreamsApp:
    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
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
            pipeline_prefix="",
        )

    def test_set_topics(self, config: PipelineConfig, handlers: ComponentHandlers):
        class AnotherType(StreamsApp):
            _type = "test"

        streams_app = AnotherType(
            handlers=handlers,
            config=config,
            **{
                "type": "test",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
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

    def test_no_empty_input_topic(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            handlers=handlers,
            config=config,
            **{
                "type": "test",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
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
                handlers=handlers,
                config=config,
                **{
                    "type": "streams-app",
                    "name": "example-name",
                    "app": {
                        "namespace": "test-namespace",
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
                handlers=handlers,
                config=config,
                **{
                    "type": "streams-app",
                    "name": "example-name",
                    "app": {
                        "namespace": "test-namespace",
                        "streams": {"brokers": "fake-broker:9092"},
                    },
                    "from": {"topics": {"example.*": {"type": "extra-pattern"}}},
                },
            )

    def test_set_streams_output_from_to(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            handlers=handlers,
            config=config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
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
        assert streams_app.app.streams.output_topic == "streams-app-output-topic"
        assert streams_app.app.streams.error_topic == "streams-app-error-topic"

    def test_weave_inputs_from_prev_component(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        streams_app = StreamsApp(
            handlers=handlers,
            config=config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
            },
        )

        streams_app.weave_from_topics(
            ToSection(
                topics={
                    "prev-output-topic": TopicConfig(
                        type=OutputTopicTypes.OUTPUT, partitions_count=10
                    ),
                    "b": TopicConfig(type=OutputTopicTypes.OUTPUT, partitions_count=10),
                    "a": TopicConfig(type=OutputTopicTypes.OUTPUT, partitions_count=10),
                    "prev-error-topic": TopicConfig(
                        type=OutputTopicTypes.ERROR, partitions_count=10
                    ),
                }
            )
        )

        assert streams_app.app.streams.input_topics == ["prev-output-topic", "b", "a"]

    def test_deploy_order(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        streams_app = StreamsApp(
            handlers=handlers,
            config=config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "version": "2.4.2",
                "app": {
                    "namespace": "test-namespace",
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
        streams_app.handlers = MagicMock()
        mock_create_topics = mocker.patch.object(
            streams_app.handlers.topic_handler, "create_topics"
        )
        mock_helm_upgrade_install = mocker.patch.object(
            streams_app.helm_wrapper, "upgrade_install"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_create_topics, "mock_create_topics")
        mock.attach_mock(mock_helm_upgrade_install, "mock_helm_upgrade_install")

        streams_app.deploy(dry_run=True)

        mock.assert_has_calls(
            [
                mocker.call.mock_create_topics(to_section=streams_app.to, dry_run=True),
                mocker.call.mock_helm_upgrade_install(
                    "example-name",
                    "bakdata-streams-bootstrap/streams-app",
                    True,
                    "test-namespace",
                    {
                        "namespace": "test-namespace",
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "streams-app-output-topic",
                            "errorTopic": "streams-app-error-topic",
                        },
                    },
                    HelmUpgradeInstallFlags(
                        force=False,
                        repo_auth_flags=RepoAuthFlags(
                            username=None,
                            password=None,
                            ca_file=None,
                            insecure_skip_tls_verify=False,
                        ),
                        timeout="5m0s",
                        version="2.4.2",
                        wait=True,
                        wait_for_jobs=False,
                    ),
                ),
            ],
            any_order=False,
        )

    def test_destroy(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        streams_app = StreamsApp(
            handlers=handlers,
            config=config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "version": "2.4.2",
                "app": {
                    "namespace": "test-namespace",
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
        streams_app.handlers = MagicMock()
        mock_helm_uninstall = mocker.patch.object(streams_app.helm_wrapper, "uninstall")

        streams_app.destroy(dry_run=True, clean=False, delete_outputs=False)

        mock_helm_uninstall.assert_called_once_with(
            "test-namespace", "example-name", True
        )

    # TODO: Assert schema deletion
    def test_should_clean_streams_app_and_deploy_clean_up_job_and_delete_clean_up(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        config.clean_streams_apps_schemas = True

        streams_app = StreamsApp(
            handlers=handlers,
            config=config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "version": "2.4.2",
                "app": {
                    "namespace": "test-namespace",
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
        mock_helm_upgrade_install = mocker.patch.object(
            streams_app.helm_wrapper, "upgrade_install"
        )
        mock_helm_uninstall = mocker.patch.object(streams_app.helm_wrapper, "uninstall")

        mock_delete_schemas = mocker.patch.object(
            handlers.schema_handler, "delete_schemas"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_helm_upgrade_install, "helm_upgrade_install")
        mock.attach_mock(mock_helm_uninstall, "helm_uninstall")
        mock.attach_mock(mock_delete_schemas, "delete_schemas")

        streams_app.destroy(dry_run=True, clean=True, delete_outputs=True)

        mock_delete_schemas.assert_called_once()

        mock.assert_has_calls(
            [
                mocker.call.helm_uninstall("test-namespace", "example-name", True),
                mocker.call.helm_uninstall(
                    "test-namespace", "example-name-clean", True
                ),
                mocker.call.helm_upgrade_install(
                    "example-name-clean",
                    "bakdata-streams-bootstrap/streams-app-cleanup-job",
                    True,
                    "test-namespace",
                    {
                        "namespace": "test-namespace",
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "streams-app-output-topic",
                            "deleteOutput": True,
                        },
                    },
                    HelmUpgradeInstallFlags(
                        version="2.4.2", wait=True, wait_for_jobs=True
                    ),
                ),
                mocker.call.helm_uninstall(
                    "test-namespace", "example-name-clean", True
                ),
                mocker.call.delete_schemas(
                    ToSection(
                        topics={
                            "streams-app-output-topic": TopicConfig(
                                type=OutputTopicTypes.OUTPUT,
                                partitions_count=10,
                            )
                        },
                    ),
                    True,
                ),
            ]
        )
