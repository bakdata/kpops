from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.kafka_connect.exception import (
    ConnectorNotFoundException,
    ConnectorStateException,
)
from kpops.component_handlers.kafka_connect.kafka_connect_handler import (
    KafkaConnectHandler,
)
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectConfig,
    KafkaConnectResponse,
)
from kpops.utils.colorify import magentaify

CONNECTOR_NAME = "test-connector-with-long-name-0123456789abcdefghijklmnop"
CONNECTOR_CLEAN_NAME = "test-connector-with-long-name-0123456789abcdef-clean"


class TestConnectorHandler:
    @pytest.fixture
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.log.info"
        )

    @pytest.fixture
    def log_warning_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.log.warning"
        )

    @pytest.fixture
    def log_error_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.log.error"
        )

    @pytest.fixture
    def renderer_diff_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.render_diff"
        )

    @staticmethod
    def connector_handler(connect_wrapper: MagicMock) -> KafkaConnectHandler:
        return KafkaConnectHandler(
            connect_wrapper=connect_wrapper,
            timeout=0,
        )

    @pytest.mark.asyncio
    async def test_should_create_connector_in_dry_run(
        self,
        renderer_diff_mock: MagicMock,
        log_info_mock: MagicMock,
    ):
        connector_wrapper = AsyncMock()
        handler = self.connector_handler(connector_wrapper)
        renderer_diff_mock.return_value = None

        config = KafkaConnectConfig()
        await handler.create_connector(CONNECTOR_NAME, config, True)
        connector_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connector_wrapper.validate_connector_config.assert_called_once_with(
            CONNECTOR_NAME, config
        )

        assert log_info_mock.mock_calls == [
            mock.call.log_info(
                f"Connector Creation: connector {CONNECTOR_NAME} already exists."
            ),
            mock.call.log_info(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    @pytest.mark.asyncio
    async def test_should_log_correct_message_when_create_connector_and_connector_not_exists_in_dry_run(
        self,
        log_info_mock: MagicMock,
    ):
        connector_wrapper = AsyncMock()
        handler = self.connector_handler(connector_wrapper)

        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
        }
        config = KafkaConnectConfig(**configs)
        await handler.create_connector(CONNECTOR_NAME, config, True)
        connector_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connector_wrapper.validate_connector_config.assert_called_once_with(
            CONNECTOR_NAME, config
        )

        assert log_info_mock.mock_calls == [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} does not exist. Creating connector with config:\n\x1b[32m+ connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n\x1b[0m\x1b[32m+ tasks.max: '1'\n\x1b[0m\x1b[32m+ topics: test-topic\n\x1b[0m"
            ),
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    @pytest.mark.asyncio
    async def test_should_log_correct_message_when_create_connector_and_connector_exists_in_dry_run(
        self,
        log_info_mock: MagicMock,
    ):
        connector_wrapper = AsyncMock()
        handler = self.connector_handler(connector_wrapper)

        actual_response = {
            "name": "name",
            "config": {
                "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
                "tasks.max": "1",
                "topics": "test-topic",
                "name": CONNECTOR_NAME,
            },
            "tasks": [],
        }
        connector_wrapper.get_connector.return_value = KafkaConnectResponse(
            **actual_response
        )

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "2",
            "topics": "test-topic",
        }
        config = KafkaConnectConfig(**configs)
        await handler.create_connector(CONNECTOR_NAME, config, True)
        connector_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connector_wrapper.validate_connector_config.assert_called_once_with(
            CONNECTOR_NAME, config
        )

        assert log_info_mock.mock_calls == [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} already exists."
            ),
            mock.call(
                f"Updating config:\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: test-topic\n"
            ),
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    @pytest.mark.asyncio
    async def test_should_log_invalid_config_when_create_connector_in_dry_run(
        self, renderer_diff_mock: MagicMock
    ):
        connector_wrapper = AsyncMock()

        errors = [
            "Missing required configuration file which has no default value.",
            "Missing connector name.",
        ]
        connector_wrapper.validate_connector_config.return_value = errors

        handler = self.connector_handler(connector_wrapper)

        config = KafkaConnectConfig()

        formatted_errors = "\n".join(errors)

        with pytest.raises(
            ConnectorStateException,
            match=f"Connector Creation: validating the connector config for connector {CONNECTOR_NAME} resulted in the following errors: {formatted_errors}",
        ):
            await handler.create_connector(CONNECTOR_NAME, config, True)

        connector_wrapper.validate_connector_config.assert_called_once_with(
            CONNECTOR_NAME, config
        )

    @pytest.mark.asyncio
    async def test_should_call_update_connector_config_when_connector_exists_not_dry_run(
        self,
    ):
        connector_wrapper = AsyncMock()
        handler = self.connector_handler(connector_wrapper)

        config = KafkaConnectConfig()
        await handler.create_connector(CONNECTOR_NAME, config, False)

        assert connector_wrapper.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.update_connector_config(CONNECTOR_NAME, config),
        ]

    @pytest.mark.asyncio
    async def test_should_call_create_connector_when_connector_does_not_exists_not_dry_run(
        self,
    ):
        connector_wrapper = AsyncMock()

        handler = self.connector_handler(connector_wrapper)

        config = KafkaConnectConfig()
        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()
        await handler.create_connector(CONNECTOR_NAME, config, False)

        connector_wrapper.create_connector.assert_called_once_with(
            CONNECTOR_NAME, config
        )

    @pytest.mark.asyncio
    async def test_should_print_correct_log_when_destroying_connector_in_dry_run(
        self,
        log_info_mock: MagicMock,
    ):
        connector_wrapper = AsyncMock()

        handler = self.connector_handler(connector_wrapper)

        await handler.destroy_connector(CONNECTOR_NAME, True)

        log_info_mock.assert_called_once_with(
            magentaify(
                f"Connector Destruction: connector {CONNECTOR_NAME} already exists. Deleting connector."
            )
        )

    @pytest.mark.asyncio
    async def test_should_print_correct_warning_log_when_destroying_connector_and_connector_exists_in_dry_run(
        self,
        log_warning_mock: MagicMock,
    ):
        connector_wrapper = AsyncMock()
        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()

        handler = self.connector_handler(connector_wrapper)

        await handler.destroy_connector(CONNECTOR_NAME, True)

        log_warning_mock.assert_called_once_with(
            f"Connector Destruction: connector {CONNECTOR_NAME} does not exist and cannot be deleted. Skipping."
        )

    @pytest.mark.asyncio
    async def test_should_call_delete_connector_when_destroying_existing_connector_not_dry_run(
        self,
    ):
        connector_wrapper = AsyncMock()
        handler = self.connector_handler(connector_wrapper)

        await handler.destroy_connector(CONNECTOR_NAME, False)
        assert connector_wrapper.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.delete_connector(CONNECTOR_NAME),
        ]

    @pytest.mark.asyncio
    async def test_should_print_correct_warning_log_when_destroying_connector_and_connector_exists_not_dry_run(
        self,
        log_warning_mock: MagicMock,
    ):
        connector_wrapper = AsyncMock()
        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()
        handler = self.connector_handler(connector_wrapper)

        await handler.destroy_connector(CONNECTOR_NAME, False)

        log_warning_mock.assert_called_once_with(
            f"Connector Destruction: the connector {CONNECTOR_NAME} does not exist. Skipping."
        )
