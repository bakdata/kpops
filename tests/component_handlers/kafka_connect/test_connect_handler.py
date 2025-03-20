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
    ConnectorCurrentState,
    ConnectorNewState,
    ConnectorResponse,
    ConnectorStatus,
    ConnectorStatusResponse,
    KafkaConnectorConfig,
    KafkaConnectorType,
)
from kpops.utils.colorify import magentaify
from tests.components.test_kafka_connector import CONNECTOR_NAME

TOPIC_NAME = "test-topic"


class TestConnectorHandler:
    @pytest.fixture()
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.log.info"
        )

    @pytest.fixture()
    def log_warning_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.log.warning"
        )

    @pytest.fixture()
    def log_error_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.log.error"
        )

    @pytest.fixture()
    def connect_wrapper(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture()
    def renderer_diff_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.render_diff"
        )

    @pytest.fixture()
    def handler(self, connect_wrapper: AsyncMock) -> KafkaConnectHandler:
        return KafkaConnectHandler(connect_wrapper=connect_wrapper)

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig(
            connector_class="com.bakdata.connect.TestConnector",
            name=CONNECTOR_NAME,
        )

    @pytest.mark.parametrize("state", [None, *ConnectorNewState])
    async def test_create_connector_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_info_mock: MagicMock,
        state: ConnectorNewState | None,
    ):
        connect_wrapper.get_connector.side_effect = ConnectorNotFoundException()

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": CONNECTOR_NAME,
            "tasks.max": "1",
            "topics": TOPIC_NAME,
        }

        config = KafkaConnectorConfig.model_validate(configs)
        await handler.create_connector(config, state=state, dry_run=True)
        connect_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connect_wrapper.validate_connector_config.assert_called_once_with(config)

        assert log_info_mock.mock_calls == [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} does not exist. Creating connector {f'in {state.value} state ' if state else ''}with config:\n\x1b[32m+ connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n\x1b[0m\x1b[32m+ name: {CONNECTOR_NAME}\n\x1b[0m\x1b[32m+ tasks.max: '1'\n\x1b[0m\x1b[32m+ topics: {TOPIC_NAME}\n\x1b[0m"
            ),
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    async def test_create_connector_dry_run_connector_exists(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        renderer_diff_mock: MagicMock,
        log_info_mock: MagicMock,
    ):
        renderer_diff_mock.return_value = None

        await handler.create_connector(connector_config, state=None, dry_run=True)
        connect_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connect_wrapper.validate_connector_config.assert_called_once_with(
            connector_config
        )

        assert log_info_mock.mock_calls == [
            mock.call.log_info(
                f"Connector Creation: connector {CONNECTOR_NAME} already exists."
            ),
            mock.call.log_info(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    async def test_log_correct_message_when_create_connector_and_connector_not_exists_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_info_mock: MagicMock,
    ):
        connect_wrapper.get_connector.side_effect = ConnectorNotFoundException()

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": CONNECTOR_NAME,
            "tasks.max": "1",
            "topics": TOPIC_NAME,
        }

        config = KafkaConnectorConfig.model_validate(configs)
        await handler.create_connector(config, state=None, dry_run=True)
        connect_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connect_wrapper.validate_connector_config.assert_called_once_with(config)

        assert log_info_mock.mock_calls == [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} does not exist. Creating connector with config:\n\x1b[32m+ connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n\x1b[0m\x1b[32m+ name: {CONNECTOR_NAME}\n\x1b[0m\x1b[32m+ tasks.max: '1'\n\x1b[0m\x1b[32m+ topics: {TOPIC_NAME}\n\x1b[0m"
            ),
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    @pytest.fixture
    def mock_get_connector(self, connect_wrapper: AsyncMock) -> None:
        connect_wrapper.get_connector.return_value = ConnectorResponse.model_validate(
            {
                "name": "name",
                "config": {
                    "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
                    "name": CONNECTOR_NAME,
                    "tasks.max": "1",
                    "topics": TOPIC_NAME,
                },
                "tasks": [],
                "type": "sink",
            }
        )

    @pytest.fixture
    def connector_config_update(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig.model_validate(
            {
                "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
                "name": CONNECTOR_NAME,
                "tasks.max": "2",
                "topics": TOPIC_NAME,
            }
        )

    @pytest.mark.parametrize("current_state", list(ConnectorCurrentState))
    @pytest.mark.usefixtures("mock_get_connector")
    async def test_update_connector_state_unchanged_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_info_mock: MagicMock,
        connector_config_update: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ):
        self.mock_connector_status(connect_wrapper, CONNECTOR_NAME, current_state)
        await handler.create_connector(
            connector_config_update, state=None, dry_run=True
        )
        connect_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connect_wrapper.validate_connector_config.assert_called_once_with(
            connector_config_update
        )

        assert log_info_mock.mock_calls == [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} already exists."
            ),
            mock.call(
                f"Updating config:\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n"
            ),
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    @pytest.mark.parametrize("state", list(ConnectorNewState))
    @pytest.mark.usefixtures("mock_get_connector")
    async def test_update_connector_same_state_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_info_mock: MagicMock,
        connector_config_update: KafkaConnectorConfig,
        state: ConnectorNewState,
    ):
        self.mock_connector_status(connect_wrapper, CONNECTOR_NAME, state.api_enum)
        await handler.create_connector(
            connector_config_update, state=state, dry_run=True
        )
        assert log_info_mock.mock_calls == [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} already exists."
            ),
            mock.call(
                f"Updating config:\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n"
            ),
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    @pytest.mark.parametrize("current_state", list(ConnectorCurrentState))
    @pytest.mark.usefixtures("mock_get_connector")
    async def test_update_and_resume_connector_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_info_mock: MagicMock,
        connector_config_update: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ):
        self.mock_connector_status(connect_wrapper, CONNECTOR_NAME, current_state)
        await handler.create_connector(
            connector_config_update, state=ConnectorNewState.RUNNING, dry_run=True
        )
        expected_calls = [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} already exists."
            ),
            mock.call(
                f"Updating config:\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n"
            ),
        ]
        if current_state is not ConnectorCurrentState.RUNNING:
            expected_calls.append(mock.call("Resuming connector"))
        expected_calls.append(
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            )
        )
        assert log_info_mock.mock_calls == expected_calls

    @pytest.mark.usefixtures("mock_get_connector")
    async def test_update_and_pause_connector_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_info_mock: MagicMock,
        connector_config_update: KafkaConnectorConfig,
    ):
        self.mock_connector_status(
            connect_wrapper, CONNECTOR_NAME, ConnectorCurrentState.RUNNING
        )
        await handler.create_connector(
            connector_config_update, state=ConnectorNewState.PAUSED, dry_run=True
        )
        assert log_info_mock.mock_calls == [
            mock.call(
                f"Connector Creation: connector {CONNECTOR_NAME} already exists."
            ),
            mock.call("Pausing connector"),
            mock.call(
                f"Updating config:\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n"
            ),
            mock.call(
                f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
            ),
        ]

    @pytest.mark.usefixtures("renderer_diff_mock")
    async def test_log_invalid_config_when_create_connector_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ):
        errors = [
            "Missing required configuration file which has no default value.",
            "Missing connector name.",
        ]
        connect_wrapper.validate_connector_config.return_value = errors
        formatted_errors = "\n".join(errors)

        with pytest.raises(
            ConnectorStateException,
            match=f"Connector Creation: validating the connector config for connector {CONNECTOR_NAME} resulted in the following errors: {formatted_errors}",
        ):
            await handler.create_connector(connector_config, state=None, dry_run=True)

        connect_wrapper.validate_connector_config.assert_called_once_with(
            connector_config
        )

    @staticmethod
    def mock_connector_status(
        connect_wrapper: AsyncMock,
        connector_name: str,
        current_state: ConnectorCurrentState,
    ) -> None:
        connect_wrapper.get_connector_status.return_value = ConnectorStatusResponse(
            name=connector_name,
            connector=ConnectorStatus(state=current_state, worker_id="foo"),
            tasks=[],
            type=KafkaConnectorType.SINK,
        )

    @pytest.mark.parametrize("current_state", list(ConnectorCurrentState))
    async def test_update_connector_state_unchanged(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ):
        self.mock_connector_status(
            connect_wrapper, connector_config.name, current_state
        )
        await handler.create_connector(connector_config, state=None, dry_run=False)
        assert connect_wrapper.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.update_connector_config(connector_config),
        ]

    @pytest.mark.parametrize("state", list(ConnectorNewState))
    async def test_update_connector_same_state(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        state: ConnectorNewState,
    ):
        self.mock_connector_status(
            connect_wrapper, connector_config.name, state.api_enum
        )
        await handler.create_connector(connector_config, state=state, dry_run=False)
        assert connect_wrapper.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.update_connector_config(connector_config),
        ]

    @pytest.mark.parametrize("current_state", list(ConnectorCurrentState))
    async def test_update_and_resume_connector(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ):
        self.mock_connector_status(
            connect_wrapper, connector_config.name, current_state
        )
        await handler.create_connector(
            connector_config, state=ConnectorNewState.RUNNING, dry_run=False
        )
        expected_calls = [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.update_connector_config(connector_config),
        ]
        if current_state is not ConnectorCurrentState.RUNNING:
            expected_calls.append(mock.call.resume_connector(connector_config.name))
        assert connect_wrapper.mock_calls == expected_calls

    async def test_update_and_pause_connector(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ):
        self.mock_connector_status(
            connect_wrapper, connector_config.name, ConnectorCurrentState.RUNNING
        )
        await handler.create_connector(
            connector_config, state=ConnectorNewState.PAUSED, dry_run=False
        )
        assert connect_wrapper.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.pause_connector(connector_config.name),
            mock.call.update_connector_config(connector_config),
        ]

    async def test_call_create_connector_when_connector_does_not_exists(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ):
        connect_wrapper.get_connector.side_effect = ConnectorNotFoundException()
        await handler.create_connector(connector_config, state=None, dry_run=False)
        connect_wrapper.create_connector.assert_called_once_with(connector_config, None)

    async def test_print_correct_log_when_destroying_connector_dry_run(
        self, handler: KafkaConnectHandler, log_info_mock: MagicMock
    ):
        await handler.destroy_connector(CONNECTOR_NAME, dry_run=True)
        log_info_mock.assert_called_once_with(
            magentaify(
                f"Connector Destruction: connector {CONNECTOR_NAME} already exists. Deleting connector."
            )
        )

    async def test_print_correct_warning_log_when_destroying_connector_and_connector_exists_dry_run(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_warning_mock: MagicMock,
    ):
        connect_wrapper.get_connector.side_effect = ConnectorNotFoundException()
        await handler.destroy_connector(CONNECTOR_NAME, dry_run=True)
        log_warning_mock.assert_called_once_with(
            f"Connector Destruction: connector {CONNECTOR_NAME} does not exist and cannot be deleted. Skipping."
        )

    async def test_call_delete_connector_when_destroying_existing_connector(
        self, connect_wrapper: AsyncMock, handler: KafkaConnectHandler
    ):
        await handler.destroy_connector(CONNECTOR_NAME, dry_run=False)
        assert connect_wrapper.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.delete_connector(CONNECTOR_NAME),
        ]

    async def test_print_correct_warning_log_when_destroying_connector_and_connector_exists(
        self,
        connect_wrapper: AsyncMock,
        handler: KafkaConnectHandler,
        log_warning_mock: MagicMock,
    ):
        connect_wrapper.get_connector.side_effect = ConnectorNotFoundException()
        await handler.destroy_connector(CONNECTOR_NAME, dry_run=False)
        log_warning_mock.assert_called_once_with(
            f"Connector Destruction: the connector {CONNECTOR_NAME} does not exist. Skipping."
        )
