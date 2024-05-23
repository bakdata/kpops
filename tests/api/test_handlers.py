from pytest_mock import MockerFixture

from kpops.api import setup_handlers
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.schema_handler.schema_handler import SchemaHandler
from kpops.component_handlers.topic.handler import TopicHandler
from kpops.config import KpopsConfig, SchemaRegistryConfig
from tests.cli.resources.custom_module import CustomSchemaProvider

HANDLER_MODULE = "kpops.api"

MODULE = CustomSchemaProvider.__module__


def test_set_up_handlers_with_no_schema_handler(mocker: MockerFixture):
    config = KpopsConfig(
        kafka_brokers="broker:9092",
        components_module=MODULE,
    )
    connector_handler_mock = mocker.patch(f"{HANDLER_MODULE}.KafkaConnectHandler")
    connector_handler = KafkaConnectHandler.from_kpops_config(config)
    connector_handler_mock.from_kpops_config.return_value = connector_handler

    topic_handler_mock = mocker.patch(f"{HANDLER_MODULE}.TopicHandler")
    wrapper = mocker.patch(f"{HANDLER_MODULE}.ProxyWrapper")
    topic_handler = TopicHandler(wrapper)
    topic_handler_mock.return_value = topic_handler

    expected = ComponentHandlers(
        schema_handler=None,
        connector_handler=connector_handler,
        topic_handler=topic_handler,
    )

    actual_handlers = setup_handlers(config)

    connector_handler_mock.from_kpops_config.assert_called_once_with(config)

    assert actual_handlers.schema_handler == expected.schema_handler
    assert actual_handlers.connector_handler == expected.connector_handler
    assert actual_handlers.topic_handler == expected.topic_handler

    assert actual_handlers.schema_handler is None
    assert isinstance(actual_handlers.connector_handler, KafkaConnectHandler)
    assert isinstance(actual_handlers.topic_handler, TopicHandler)


def test_set_up_handlers_with_schema_handler(mocker: MockerFixture):
    config = KpopsConfig(
        schema_registry=SchemaRegistryConfig(enabled=True),
        kafka_brokers="broker:9092",
    )
    schema_handler_mock = mocker.patch(f"{HANDLER_MODULE}.SchemaHandler")
    schema_handler = SchemaHandler.load_schema_handler(config)
    schema_handler_mock.load_schema_handler.return_value = schema_handler

    connector_handler_mock = mocker.patch(f"{HANDLER_MODULE}.KafkaConnectHandler")
    connector_handler = KafkaConnectHandler.from_kpops_config(config)
    connector_handler_mock.from_kpops_config.return_value = connector_handler

    topic_handler_mock = mocker.patch(f"{HANDLER_MODULE}.TopicHandler")
    wrapper = mocker.patch(f"{HANDLER_MODULE}.ProxyWrapper")
    topic_handler = TopicHandler(wrapper)
    topic_handler_mock.return_value = topic_handler

    expected = ComponentHandlers(
        schema_handler=schema_handler,
        connector_handler=connector_handler,
        topic_handler=topic_handler,
    )

    actual_handlers = setup_handlers(config)

    schema_handler_mock.load_schema_handler.assert_called_once_with(config)

    connector_handler_mock.from_kpops_config.assert_called_once_with(config)

    assert actual_handlers.schema_handler == expected.schema_handler
    assert actual_handlers.connector_handler == expected.connector_handler
    assert actual_handlers.topic_handler == expected.topic_handler

    assert isinstance(actual_handlers.schema_handler, SchemaHandler)
    assert isinstance(actual_handlers.connector_handler, KafkaConnectHandler)
    assert isinstance(actual_handlers.topic_handler, TopicHandler)
