from unittest import mock

import pytest

from kpops.component_handlers import ComponentHandlers
from kpops.config import KpopsConfig, TopicNameConfig, set_config
from tests.components import PIPELINE_BASE_DIR


@pytest.fixture(autouse=True, scope="module")
def config() -> None:
    config = KpopsConfig(
        topic_name_config=TopicNameConfig(
            default_error_topic_name="${component.type}-error-topic",
            default_output_topic_name="${component.type}-output-topic",
        ),
        kafka_brokers="broker:9092",
        pipeline_base_dir=PIPELINE_BASE_DIR,
    )
    set_config(config)


@pytest.fixture(autouse=True, scope="module")
def handlers() -> None:
    ComponentHandlers(
        schema_handler=mock.AsyncMock(),
        connector_handler=mock.AsyncMock(),
        topic_handler=mock.AsyncMock(),
    )
