import re
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from structlog.testing import capture_logs

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
    def kafka_connect(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture()
    def renderer_diff_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.component_handlers.kafka_connect.kafka_connect_handler.render_diff"
        )

    @pytest.fixture()
    def handler(self, kafka_connect: AsyncMock) -> KafkaConnectHandler:
        return KafkaConnectHandler(kafka_connect=kafka_connect)

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig(
            connector_class="com.bakdata.connect.TestConnector",
            name=CONNECTOR_NAME,
        )

    @pytest.mark.parametrize("state", [None, *ConnectorNewState])
    async def test_create_connector_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        state: ConnectorNewState | None,
    ) -> None:
        kafka_connect.get_connector.side_effect = ConnectorNotFoundException()

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": CONNECTOR_NAME,
            "tasks.max": "1",
            "topics": TOPIC_NAME,
        }

        config = KafkaConnectorConfig.model_validate(configs)
        with capture_logs() as cap_logs:
            await handler.create_connector(config, state=state, dry_run=True)
        kafka_connect.get_connector.assert_called_once_with(CONNECTOR_NAME)
        kafka_connect.validate_connector_config.assert_called_once_with(config)

        assert {
            "event": "Connector does not exist. Creating connector",
            "connector_name": CONNECTOR_NAME,
            "state": state.value if state else None,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": f"\n\x1b[32m+ connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n\x1b[0m\x1b[32m+ name: {CONNECTOR_NAME}\n\x1b[0m\x1b[32m+ tasks.max: '1'\n\x1b[0m\x1b[32m+ topics: {TOPIC_NAME}\n\x1b[0m",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs

    async def test_create_connector_dry_run_connector_exists(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        renderer_diff_mock: MagicMock,
    ) -> None:
        renderer_diff_mock.return_value = None
        kafka_connect.get_connector.return_value = ConnectorResponse(
            name=CONNECTOR_NAME,
            config=connector_config,
            tasks=[],
            type=KafkaConnectorType.SINK,
        )

        with capture_logs() as cap_logs:
            await handler.create_connector(connector_config, state=None, dry_run=True)
        kafka_connect.get_connector.assert_called_once_with(CONNECTOR_NAME)
        kafka_connect.validate_connector_config.assert_called_once_with(
            connector_config
        )

        assert {
            "event": "Connector already exists.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs

    async def test_log_correct_message_when_create_connector_and_connector_not_exists_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
    ) -> None:
        kafka_connect.get_connector.side_effect = ConnectorNotFoundException()

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": CONNECTOR_NAME,
            "tasks.max": "1",
            "topics": TOPIC_NAME,
        }

        config = KafkaConnectorConfig.model_validate(configs)
        with capture_logs() as cap_logs:
            await handler.create_connector(config, state=None, dry_run=True)
        kafka_connect.get_connector.assert_called_once_with(CONNECTOR_NAME)
        kafka_connect.validate_connector_config.assert_called_once_with(config)

        assert {
            "event": "Connector does not exist. Creating connector",
            "connector_name": CONNECTOR_NAME,
            "state": None,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": f"\n\x1b[32m+ connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n\x1b[0m\x1b[32m+ name: {CONNECTOR_NAME}\n\x1b[0m\x1b[32m+ tasks.max: '1'\n\x1b[0m\x1b[32m+ topics: {TOPIC_NAME}\n\x1b[0m",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs

    @pytest.fixture
    def mock_get_connector(self, kafka_connect: AsyncMock) -> None:
        kafka_connect.get_connector.return_value = ConnectorResponse.model_validate(
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
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config_update: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ) -> None:
        self.mock_connector_status(kafka_connect, CONNECTOR_NAME, current_state)
        with capture_logs() as cap_logs:
            await handler.create_connector(
                connector_config_update, state=None, dry_run=True
            )
        kafka_connect.get_connector.assert_called_once_with(CONNECTOR_NAME)
        kafka_connect.validate_connector_config.assert_called_once_with(
            connector_config_update
        )

        assert {
            "event": "Connector already exists.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Updating config",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": f"\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs

    @pytest.mark.parametrize("state", list(ConnectorNewState))
    @pytest.mark.usefixtures("mock_get_connector")
    async def test_update_connector_same_state_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config_update: KafkaConnectorConfig,
        state: ConnectorNewState,
    ) -> None:
        self.mock_connector_status(kafka_connect, CONNECTOR_NAME, state.api_enum)
        with capture_logs() as cap_logs:
            await handler.create_connector(
                connector_config_update, state=state, dry_run=True
            )
        assert {
            "event": "Connector already exists.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Updating config",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": f"\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs

    @pytest.mark.parametrize("current_state", list(ConnectorCurrentState))
    @pytest.mark.usefixtures("mock_get_connector")
    async def test_update_and_resume_connector_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config_update: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ) -> None:
        self.mock_connector_status(kafka_connect, CONNECTOR_NAME, current_state)
        with capture_logs() as cap_logs:
            await handler.create_connector(
                connector_config_update, state=ConnectorNewState.RUNNING, dry_run=True
            )
        assert {
            "event": "Connector already exists.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Updating config",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": f"\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n",
            "log_level": "info",
        } in cap_logs
        if current_state is not ConnectorCurrentState.RUNNING:
            assert {
                "event": "Resuming connector",
                "connector_name": CONNECTOR_NAME,
                "log_level": "info",
            } in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs

    @pytest.mark.usefixtures("mock_get_connector")
    async def test_update_and_pause_connector_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config_update: KafkaConnectorConfig,
    ) -> None:
        self.mock_connector_status(
            kafka_connect, CONNECTOR_NAME, ConnectorCurrentState.RUNNING
        )
        with capture_logs() as cap_logs:
            await handler.create_connector(
                connector_config_update, state=ConnectorNewState.PAUSED, dry_run=True
            )
        assert {
            "event": "Connector already exists.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Pausing connector",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Updating config",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": f"\n  connector.class: org.apache.kafka.connect.file.FileStreamSinkConnector\n  name: {CONNECTOR_NAME}\n\x1b[31m- tasks.max: '1'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m\x1b[32m+ tasks.max: '2'\n\x1b[0m\x1b[33m?             ^\n\x1b[0m  topics: {TOPIC_NAME}\n",
            "log_level": "info",
        } in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs

    @pytest.mark.usefixtures("renderer_diff_mock")
    async def test_log_invalid_config_when_create_connector_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        errors = [
            "Missing required configuration file which has no default value.",
            "Missing connector name.",
        ]
        kafka_connect.validate_connector_config.return_value = errors
        kafka_connect.get_connector.return_value = ConnectorResponse(
            name=CONNECTOR_NAME,
            config=connector_config,
            tasks=[],
            type=KafkaConnectorType.SINK,
        )
        formatted_errors = "\n".join(errors)

        with pytest.raises(
            ConnectorStateException,
            match=re.escape(
                f"Connector Creation: validating the connector config for connector {CONNECTOR_NAME} resulted in the following errors: {formatted_errors}"
            ),
        ):
            await handler.create_connector(connector_config, state=None, dry_run=True)

        kafka_connect.validate_connector_config.assert_called_once_with(
            connector_config
        )

    @staticmethod
    def mock_connector_status(
        kafka_connect: AsyncMock,
        connector_name: str,
        current_state: ConnectorCurrentState,
    ) -> None:
        kafka_connect.get_connector_status.return_value = ConnectorStatusResponse(
            name=connector_name,
            connector=ConnectorStatus(state=current_state, worker_id="foo"),
            tasks=[],
            type=KafkaConnectorType.SINK,
        )

    @pytest.mark.parametrize("current_state", list(ConnectorCurrentState))
    async def test_update_connector_state_unchanged(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ) -> None:
        self.mock_connector_status(kafka_connect, connector_config.name, current_state)
        await handler.create_connector(connector_config, state=None, dry_run=False)
        assert kafka_connect.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.update_connector_config(connector_config, dry_run=False),
        ]

    @pytest.mark.parametrize("state", list(ConnectorNewState))
    async def test_update_connector_same_state(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        state: ConnectorNewState,
    ) -> None:
        self.mock_connector_status(kafka_connect, connector_config.name, state.api_enum)
        await handler.create_connector(connector_config, state=state, dry_run=False)
        assert kafka_connect.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.update_connector_config(connector_config, dry_run=False),
        ]

    @pytest.mark.parametrize("current_state", list(ConnectorCurrentState))
    async def test_update_and_resume_connector(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        current_state: ConnectorCurrentState,
    ) -> None:
        self.mock_connector_status(kafka_connect, connector_config.name, current_state)
        await handler.create_connector(
            connector_config, state=ConnectorNewState.RUNNING, dry_run=False
        )
        expected_calls = [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.update_connector_config(connector_config, dry_run=False),
        ]
        if current_state is not ConnectorCurrentState.RUNNING:
            expected_calls.append(
                mock.call.resume_connector(connector_config.name, dry_run=False)
            )
        assert kafka_connect.mock_calls == expected_calls

    async def test_update_and_pause_connector(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        self.mock_connector_status(
            kafka_connect, connector_config.name, ConnectorCurrentState.RUNNING
        )
        await handler.create_connector(
            connector_config, state=ConnectorNewState.PAUSED, dry_run=False
        )
        assert kafka_connect.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector_status(CONNECTOR_NAME),
            mock.call.pause_connector(connector_config.name, dry_run=False),
            mock.call.update_connector_config(connector_config, dry_run=False),
        ]

    async def test_call_create_connector_when_connector_does_not_exists(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        kafka_connect.get_connector.side_effect = ConnectorNotFoundException()
        await handler.create_connector(connector_config, state=None, dry_run=False)
        kafka_connect.create_connector.assert_called_once_with(
            connector_config, None, dry_run=False
        )

    async def test_print_correct_log_when_destroying_connector_dry_run(
        self, handler: KafkaConnectHandler
    ) -> None:
        with capture_logs() as cap_logs:
            await handler.destroy_connector(CONNECTOR_NAME, dry_run=True)
        assert {
            "event": magentaify(
                f"Connector Destruction: connector {CONNECTOR_NAME} already exists. Deleting connector."
            ),
            "log_level": "info",
        } in cap_logs

    async def test_print_correct_warning_log_when_destroying_connector_and_connector_exists_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
    ) -> None:
        kafka_connect.get_connector.side_effect = ConnectorNotFoundException()
        with capture_logs() as cap_logs:
            await handler.destroy_connector(CONNECTOR_NAME, dry_run=True)
        assert {
            "event": "Connector does not exist and cannot be deleted. Skipping.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "warning",
        } in cap_logs

    async def test_call_delete_connector_when_destroying_existing_connector(
        self, kafka_connect: AsyncMock, handler: KafkaConnectHandler
    ) -> None:
        await handler.destroy_connector(CONNECTOR_NAME, dry_run=False)
        assert kafka_connect.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.delete_connector(CONNECTOR_NAME, dry_run=False),
        ]

    async def test_print_correct_warning_log_when_destroying_connector_and_connector_exists(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
    ) -> None:
        kafka_connect.get_connector.side_effect = ConnectorNotFoundException()
        with capture_logs() as cap_logs:
            await handler.destroy_connector(CONNECTOR_NAME, dry_run=False)
        assert {
            "event": "Connector does not exist. Skipping.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "warning",
        } in cap_logs

    async def test_reset_connector_dry_run(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        with capture_logs() as cap_logs:
            await handler.reset_connector(connector_config, dry_run=True)

        kafka_connect.get_connector.assert_called_once_with(CONNECTOR_NAME)
        kafka_connect.create_connector.assert_not_called()
        kafka_connect.stop_connector.assert_called_once_with(
            CONNECTOR_NAME, dry_run=True
        )
        kafka_connect.reset_offset.assert_called_once_with(CONNECTOR_NAME, dry_run=True)
        kafka_connect.delete_connector.assert_not_called()
        assert {
            "event": magentaify(
                f"Connector reset: resetting offsets for connector {CONNECTOR_NAME}."
            ),
            "log_level": "info",
        } in cap_logs

    async def test_reset_connector_dry_run_connector_missing(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
        renderer_diff_mock: MagicMock,
    ) -> None:
        kafka_connect.get_connector.side_effect = ConnectorNotFoundException()
        renderer_diff_mock.return_value = ""

        with capture_logs() as cap_logs:
            await handler.reset_connector(connector_config, dry_run=True)

        assert kafka_connect.get_connector.call_count == 2
        kafka_connect.validate_connector_config.assert_called_once_with(
            connector_config
        )
        kafka_connect.create_connector.assert_called_once_with(
            connector_config, ConnectorNewState.PAUSED, dry_run=True
        )
        kafka_connect.stop_connector.assert_called_once_with(
            CONNECTOR_NAME, dry_run=True
        )
        kafka_connect.reset_offset.assert_called_once_with(CONNECTOR_NAME, dry_run=True)
        kafka_connect.delete_connector.assert_called_once_with(
            CONNECTOR_NAME, dry_run=True
        )

        assert {
            "event": "Connector does not exist. Creating connector",
            "connector_name": CONNECTOR_NAME,
            "state": "paused",
            "log_level": "info",
        } in cap_logs
        assert {"event": "\n", "log_level": "info"} in cap_logs
        assert {
            "event": "Connector config is valid!",
            "connector_name": CONNECTOR_NAME,
            "log_level": "info",
        } in cap_logs
        assert {
            "event": magentaify(
                f"Connector reset: resetting offsets for connector {CONNECTOR_NAME}."
            ),
            "log_level": "info",
        } in cap_logs
        assert {
            "event": magentaify(
                f"Connector reset: deleting temporarily created connector {CONNECTOR_NAME}."
            ),
            "log_level": "info",
        } in cap_logs

    async def test_reset_connector(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        await handler.reset_connector(connector_config, dry_run=False)
        assert kafka_connect.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.stop_connector(CONNECTOR_NAME, dry_run=False),
            mock.call.reset_offset(CONNECTOR_NAME, dry_run=False),
        ]

    async def test_reset_connector_when_connector_missing(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        kafka_connect.get_connector.side_effect = ConnectorNotFoundException()

        await handler.reset_connector(connector_config, dry_run=False)

        assert kafka_connect.mock_calls == [
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.get_connector(CONNECTOR_NAME),
            mock.call.create_connector(
                connector_config, ConnectorNewState.PAUSED, dry_run=False
            ),
            mock.call.stop_connector(CONNECTOR_NAME, dry_run=False),
            mock.call.reset_offset(CONNECTOR_NAME, dry_run=False),
            mock.call.delete_connector(CONNECTOR_NAME, dry_run=False),
        ]

    async def test_reset_connector_disappears_during_reset(
        self,
        kafka_connect: AsyncMock,
        handler: KafkaConnectHandler,
        connector_config: KafkaConnectorConfig,
    ) -> None:
        """Connector existed but got deleted concurrently before it could be stopped."""
        kafka_connect.stop_connector.side_effect = ConnectorNotFoundException()

        with capture_logs() as cap_logs:
            await handler.reset_connector(connector_config, dry_run=False)

        kafka_connect.reset_offset.assert_not_called()
        assert {
            "event": "Connector does not exist. Skipping.",
            "connector_name": CONNECTOR_NAME,
            "log_level": "warning",
        } in cap_logs
