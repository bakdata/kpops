from pathlib import Path
from unittest.mock import MagicMock
import pytest
import yaml
from kpops.cli.pipeline_config import PipelineConfig, TopicNameConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig
from kpops.components.streams_bootstrap.streams.model import StreamsConfig, StreamsAppConfig
from kpops.components.streams_bootstrap.streams.streams_app import StreamsApp

@pytest.fixture()
def streams_config() -> StreamsConfig:
    return StreamsConfig(
        brokers="",
        extra_input_patterns={
            "eip1k": "eip1v",
            "eip2k": "eip2v",
        },
        extra_input_topics={
            "eit1k": ["eit1v"],
            "eit2k": ["eit2v"],
        },
    )

@pytest.fixture()
def streams_app_config(streams_config: StreamsConfig) -> StreamsAppConfig:
    return StreamsAppConfig(streams=streams_config)

STREAMS_APP_NAME = "test-streams-app-with-long-name-0123456789abcdefghijklmnop"
STREAMS_APP_CLEAN_NAME = "test-streams-app-with-long-name-0123456789abcd-clean"
DEFAULTS_PATH: Path = Path(__file__).parent

@pytest.fixture
def handlers() -> ComponentHandlers:
    return ComponentHandlers(
        schema_handler=MagicMock(),
        connector_handler=MagicMock(),
        topic_handler=MagicMock(),
    )

@pytest.fixture
def config() -> PipelineConfig:
    return PipelineConfig(
        defaults_path=DEFAULTS_PATH,
        environment="development",
        topic_name_config=TopicNameConfig(
            default_error_topic_name="${component_type}-error-topic",
            default_output_topic_name="${component_type}-output-topic",
        ),
        helm_diff_config=HelmDiffConfig(),
    )

@pytest.fixture()
def streams_app(streams_app_config: StreamsAppConfig, config: PipelineConfig, handlers: ComponentHandlers) -> StreamsApp:
    return StreamsApp(
        name=STREAMS_APP_NAME,
        namespace="namespace",
        config=config,
        handlers=handlers,
        app=streams_app_config,
    )

def test_streams_config(streams_config: StreamsConfig):
    assert streams_config.model_dump() == {
        "brokers": "",
        "extra_input_patterns": {
            "eip1k": "eip1v",
            "eip2k": "eip2v",
        },
        "extra_input_topics": {
            "eit1k": ["eit1v"],
            "eit2k": ["eit2v"],
        },
    }

def test_streams_app_config(streams_app_config: StreamsAppConfig):
    assert streams_app_config.model_dump() == {
        "autoscaling": None,
        "name_override": None,
        "streams": {
            "brokers": "",
            "extra_input_patterns": {
                "eip1k": "eip1v",
                "eip2k": "eip2v",
            },
            "extra_input_topics": {
                "eit1k": ["eit1v"],
                "eit2k": ["eit2v"],
            },
        }
    }

def test_streams_app(streams_app):
    assert streams_app.model_dump() == {
        "app": {
            "autoscaling": None,
            "name_override": None,
            "streams": {
                "brokers": "",
                "extra_input_patterns": {
                    "eip1k": "eip1v",
                    "eip2k": "eip2v",
                },
                "extra_input_topics": {
                    "eit1k": ["eit1v"],
                    "eit2k": ["eit2v"],
                },
            }
        },
    }
