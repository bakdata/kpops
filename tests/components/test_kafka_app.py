from pathlib import Path
from unittest.mock import MagicMock

import pytest

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components import KafkaApp

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestKafkaApp:
    @pytest.fixture
    def config(self) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
        )

    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    def test_default_brokers(self, config: PipelineConfig, handlers: ComponentHandlers):
        kafka_app = KafkaApp(
            handlers=handlers,
            config=config,
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
        assert kafka_app.app.streams.brokers == "fake-broker:9092"
