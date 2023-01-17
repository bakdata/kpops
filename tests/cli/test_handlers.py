from pathlib import Path

from pytest_mock import MockerFixture

from kpops.cli.main import setup_handlers
from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.topic.handler import TopicHandler
from tests.cli.resources.module import CustomSchemaProvider

MODULE = CustomSchemaProvider.__module__


def test_set_up_handlers_with_no_schema_handler(mocker: MockerFixture):
    config = PipelineConfig(
        defaults_path=Path("fake"),
        environment="development",
        kafka_rest_host="https://testhost:8082",
        schema_registry_url=None,
    )
    connector_handler_mock = mocker.patch("kpops.cli.main.KafkaConnectHandler")
    connector_handler = KafkaConnectHandler.from_pipeline_config(pipeline_config=config)
    connector_handler_mock.from_pipeline_config.return_value = connector_handler

    topic_handler_mock = mocker.patch("kpops.cli.main.TopicHandler")
    wrapper = mocker.patch("kpops.cli.main.ProxyWrapper")
    topic_handler = TopicHandler(wrapper)
    topic_handler_mock.return_value = topic_handler

    expected = ComponentHandlers(
        schema_handler=None,
        connector_handler=connector_handler,
        topic_handler=topic_handler,
    )

    actual_handlers = setup_handlers(MODULE, config)

    connector_handler_mock.from_pipeline_config.assert_called_once_with(config)

    assert actual_handlers.schema_handler == expected.schema_handler
    assert actual_handlers.connector_handler == expected.connector_handler
    assert actual_handlers.topic_handler == expected.topic_handler

    assert actual_handlers.schema_handler is None
    assert isinstance(actual_handlers.connector_handler, KafkaConnectHandler)
    assert isinstance(actual_handlers.topic_handler, TopicHandler)


def test_set_up_handlers_with_schema_handler(mocker: MockerFixture):
    config = PipelineConfig(
        defaults_path=Path("fake"),
        environment="development",
        kafka_rest_host="https://testhost:8082",
        schema_registry_url="https://testhost:8081",
    )
    schema_handler_mock = mocker.patch("kpops.cli.main.SchemaHandler")
    schema_handler = SchemaHandler.load_schema_handler(MODULE, config)
    schema_handler_mock.load_schema_handler.return_value = schema_handler

    connector_handler_mock = mocker.patch("kpops.cli.main.KafkaConnectHandler")
    connector_handler = KafkaConnectHandler.from_pipeline_config(pipeline_config=config)
    connector_handler_mock.from_pipeline_config.return_value = connector_handler

    topic_handler_mock = mocker.patch("kpops.cli.main.TopicHandler")
    wrapper = mocker.patch("kpops.cli.main.ProxyWrapper")
    topic_handler = TopicHandler(wrapper)
    topic_handler_mock.return_value = topic_handler

    expected = ComponentHandlers(
        schema_handler=schema_handler,
        connector_handler=connector_handler,
        topic_handler=topic_handler,
    )

    actual_handlers = setup_handlers(MODULE, config)

    schema_handler_mock.load_schema_handler.assert_called_once_with(MODULE, config)

    connector_handler_mock.from_pipeline_config.assert_called_once_with(config)

    assert actual_handlers.schema_handler == expected.schema_handler
    assert actual_handlers.connector_handler == expected.connector_handler
    assert actual_handlers.topic_handler == expected.topic_handler

    assert isinstance(actual_handlers.schema_handler, SchemaHandler)
    assert isinstance(actual_handlers.connector_handler, KafkaConnectHandler)
    assert isinstance(actual_handlers.topic_handler, TopicHandler)
