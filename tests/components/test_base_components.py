from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli import pipeline_config
from kpops.cli.pipeline_config import PipelineConfig, TopicNameConfig
from kpops.components.base_components import KafkaApp
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppConfig,
)
from kpops.components.base_components.models.to_section import (
    OutputTopicTypes,
    TopicConfig,
    ToSection,
)
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp
from kpops.pipeline_deployer.streams_bootstrap.streams_bootstrap_application_type import (
    ApplicationType,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


@pytest.fixture
def test_config() -> PipelineConfig:
    return pipeline_config.PipelineConfig(
        defaults_path=DEFAULTS_PATH,
        environment="development",
        topic_name_config=TopicNameConfig(
            default_error_topic_name="${component_type}-error-topic",
            default_output_topic_name="${component_type}-output-topic",
        ),
        pipeline_prefix="",
    )


class TestKubernetesApp:
    def test_name_check(self, test_config: PipelineConfig):
        app_config = KubernetesAppConfig(namespace="test")

        assert KubernetesApp(
            _type="test",
            app=app_config,
            config=test_config,
            name="example-component-with-very-long-name-longer-than-most-of-our-kubernetes-apps",
        )

        with pytest.raises(ValueError):
            assert KubernetesApp(
                _type="test",
                app=app_config,
                config=test_config,
                name="Not-Compatible*",
            )

        with pytest.raises(ValueError):
            assert KubernetesApp(
                _type="test",
                app=app_config,
                config=test_config,
                name="snake_case",
            )


class TestKafkaApp:
    def test_default_brokers(self, test_config: PipelineConfig):
        kafka_app = KafkaApp(
            config=test_config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {
                        "outputTopic": "test",
                        "brokers": "fake-broker:9092",
                    },
                },
            },
        )
        assert kafka_app.app.streams.brokers


class TestStreamsApp:
    def test_set_topics(self, test_config: PipelineConfig):
        class AnotherType(StreamsApp):
            _type = "test"

        streams_app = AnotherType(
            config=test_config,
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

    def test_no_empty_input_topic(self, test_config: PipelineConfig):
        streams_app = StreamsApp(
            config=test_config,
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

    def test_should_validate(self, test_config: PipelineConfig):
        with pytest.raises(ValueError):
            StreamsApp(
                config=test_config,
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
                config=test_config,
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

    def test_set_streams_output_from_to(self, test_config: PipelineConfig):
        streams_app = StreamsApp(
            config=test_config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${topic_name}": TopicConfig(
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

    def test_weave_inputs_from_prev_component(self, test_config: PipelineConfig):
        streams_app = StreamsApp(
            config=test_config,
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

    def test_deploy_order(self, test_config: PipelineConfig, mocker: MockerFixture):
        streams_app = StreamsApp(
            config=test_config,
            **{
                "type": "streams-app",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${topic_name}": TopicConfig(
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
        streams_app.pipeline_handlers = MagicMock()

        mock_create_topics = mocker.patch.object(
            streams_app.pipeline_handlers.topic_handler, "create_topics"
        )
        mock_install_app = mocker.patch.object(
            streams_app.pipeline_handlers.app_handler, "install_app"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_create_topics, "mock_create_topics")
        mock.attach_mock(mock_install_app, "mock_install_app")
        streams_app.deploy(dry_run=True)
        mock.assert_has_calls(
            [
                mocker.call.mock_create_topics(to_section=streams_app.to, dry_run=True),
                mocker.call.mock_install_app(
                    release_name="example-name",
                    namespace="test-namespace",
                    values={
                        "namespace": "test-namespace",
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "streams-app-output-topic",
                            "errorTopic": "streams-app-error-topic",
                        },
                    },
                    app_type=ApplicationType.STREAMS_APP,
                    dry_run=True,
                ),
            ],
            any_order=False,
        )


class TestProducerApp:
    def test_output_topics(self, test_config: PipelineConfig):
        producer_app = ProducerApp(
            config=test_config,
            **{
                "type": "producer-app",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${topic_name}": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            type=OutputTopicTypes.EXTRA,
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )

        assert producer_app.app.streams.output_topic == "producer-output-topic"
        assert producer_app.app.streams.extra_output_topics == {
            "first-extra-topic": "extra-topic-1"
        }

    def test_deploy_order(self, test_config: PipelineConfig, mocker: MockerFixture):
        streams_app = ProducerApp(
            config=test_config,
            **{
                "type": "producer-app",
                "name": "example-name",
                "app": {
                    "namespace": "test-namespace",
                    "streams": {"brokers": "fake-broker:9092"},
                },
                "to": {
                    "topics": {
                        "${topic_name}": TopicConfig(
                            type=OutputTopicTypes.OUTPUT, partitions_count=10
                        ),
                        "extra-topic-1": TopicConfig(
                            type=OutputTopicTypes.EXTRA,
                            role="first-extra-topic",
                            partitions_count=10,
                        ),
                    }
                },
            },
        )
        streams_app.pipeline_handlers = MagicMock()

        mock_install_app = mocker.patch.object(
            streams_app.pipeline_handlers.app_handler, "install_app"
        )
        mock_create_topics = mocker.patch.object(
            streams_app.pipeline_handlers.topic_handler, "create_topics"
        )

        mock = mocker.MagicMock()
        mock.attach_mock(mock_create_topics, "mock_create_topics")
        mock.attach_mock(mock_install_app, "mock_install_app")
        streams_app.deploy(dry_run=True)
        mock.assert_has_calls(
            [
                mocker.call.mock_create_topics(to_section=streams_app.to, dry_run=True),
                mocker.call.mock_install_app(
                    release_name="example-name",
                    namespace="test-namespace",
                    values={
                        "namespace": "test-namespace",
                        "streams": {
                            "brokers": "fake-broker:9092",
                            "outputTopic": "producer-output-topic",
                        },
                    },
                    app_type=ApplicationType.PRODUCER_APP,
                    dry_run=True,
                ),
            ],
            any_order=False,
        )
