import json
import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from anyio import Path
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from kpops.component_handlers.kafka_connect.connect_wrapper import ConnectWrapper
from kpops.component_handlers.kafka_connect.exception import (
    ConnectorNotFoundException,
    KafkaConnectError,
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
from kpops.config import KpopsConfig
from tests.component_handlers.kafka_connect import RESOURCES_PATH

DEFAULT_HOST = "http://localhost:8083"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
CONNECTOR_NAME = "test-connector"


class TestConnectorApiWrapper:
    @pytest.fixture()
    def connect_wrapper(self) -> ConnectWrapper:
        config = KpopsConfig.model_validate({})
        return ConnectWrapper(config.kafka_connect)

    @pytest.fixture()
    def connector_response(self) -> dict[str, Any]:
        return {
            "name": CONNECTOR_NAME,
            "type": "sink",
            "config": {
                "name": CONNECTOR_NAME,
                "connector.class": "com.bakdata.connect.TestConnector",
                "tasks.max": "10",
                "topics": "test-topic",
                "hdfs.url": "hdfs://fakehost:9000",
                "hadoop.conf.dir": "/opt/hadoop/conf",
                "hadoop.home": "/opt/hadoop",
                "flush.size": "100",
                "rotate.interval.ms": "1000",
            },
            "tasks": [
                {"connector": "hdfs-sink-connector", "task": 1},
                {"connector": "hdfs-sink-connector", "task": 2},
                {"connector": "hdfs-sink-connector", "task": 3},
            ],
        }

    @pytest.fixture()
    def connector_config(
        self, connector_response: dict[str, Any]
    ) -> KafkaConnectorConfig:
        return KafkaConnectorConfig.model_validate(connector_response["config"])

    @pytest.fixture()
    def mock_sleep(self, mocker: MockerFixture) -> None:
        mocker.patch("asyncio.sleep", return_value=None)  # skip delay

    def test_serialize_config(self):
        # all values should be converted to strings
        assert KafkaConnectorConfig.model_validate(
            {
                "name": CONNECTOR_NAME,
                "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
                "batch.size": 50,
                "max.buffered.records": 500,
                "connection.password": "fake-password",
                "store.kafka.keys": True,
                "receive.buffer.bytes": -1,
                "topic.tracking.allow.reset": False,
            }
        ).model_dump() == {
            "name": CONNECTOR_NAME,
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "batch.size": "50",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
            "store.kafka.keys": "true",
            "receive.buffer.bytes": "-1",
            "topic.tracking.allow.reset": "false",
        }

    @patch("httpx.AsyncClient.post")
    async def test_create_connector_request(
        self,
        mock_post: AsyncMock,
        connect_wrapper: ConnectWrapper,
        connector_config: KafkaConnectorConfig,
    ):
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.create_connector(connector_config)

        mock_post.assert_called_with(
            "/connectors",
            json={
                "name": CONNECTOR_NAME,
                "config": connector_config.model_dump(),
            },
        )

    @patch("httpx.AsyncClient.post")
    async def test_create_connector_request_with_initial_state(
        self,
        mock_post: AsyncMock,
        connect_wrapper: ConnectWrapper,
        connector_config: KafkaConnectorConfig,
    ):
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.create_connector(
                connector_config, ConnectorNewState.RUNNING
            )
        mock_post.assert_called_with(
            "/connectors",
            json={
                "name": CONNECTOR_NAME,
                "config": connector_config.model_dump(),
                "initial_state": "RUNNING",
            },
        )

    async def test_create_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
        connector_response: dict[str, Any],
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/connectors",
            headers=HEADERS,
            status_code=httpx.codes.CREATED,
            json=connector_response,
        )

        actual_response = await connect_wrapper.create_connector(connector_config)
        assert ConnectorResponse.model_validate(connector_response) == actual_response

    @pytest.mark.usefixtures("mock_sleep")
    async def test_create_connector_retry(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_response: dict[str, Any],
        connector_config: KafkaConnectorConfig,
        caplog: pytest.LogCaptureFixture,
    ):
        ENDPOINT = f"{DEFAULT_HOST}/connectors"
        httpx_mock.add_response(
            method="POST",
            url=ENDPOINT,
            headers=HEADERS,
            status_code=httpx.codes.CONFLICT,
            json={},
        )
        httpx_mock.add_response(
            method="POST",
            url=ENDPOINT,
            headers=HEADERS,
            status_code=httpx.codes.CREATED,
            json=connector_response,
        )

        with caplog.at_level(logging.INFO):
            await connect_wrapper.create_connector(connector_config)

        assert len(caplog.records) == 2
        assert (
            caplog.records[0].message
            == "Rebalancing in progress while creating a connector... Retrying..."
        )
        assert caplog.records[0].levelname == "WARNING"
        assert caplog.records[1].message == "Connector test-connector created."
        assert caplog.records[1].levelname == "INFO"

    async def test_get_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_response: dict[str, Any],
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            json=connector_response,
        )
        actual_response = await connect_wrapper.get_connector(CONNECTOR_NAME)
        assert ConnectorResponse.model_validate(connector_response) == actual_response

    async def test_get_connector_not_found(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            status_code=httpx.codes.NOT_FOUND,
            json={},
        )
        with pytest.raises(ConnectorNotFoundException):
            await connect_wrapper.get_connector(CONNECTOR_NAME)

    @pytest.mark.usefixtures("mock_sleep")
    async def test_get_connector_retry(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_response: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ):
        ENDPOINT = f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}"
        httpx_mock.add_response(
            method="GET",
            url=ENDPOINT,
            headers=HEADERS,
            status_code=httpx.codes.CONFLICT,
            json={},
        )
        httpx_mock.add_response(
            method="GET",
            url=ENDPOINT,
            headers=HEADERS,
            json=connector_response,
        )
        with caplog.at_level(logging.WARNING):
            actual_response = await connect_wrapper.get_connector(CONNECTOR_NAME)
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].message
            == "Rebalancing in progress while getting a connector... Retrying..."
        )
        assert actual_response == ConnectorResponse.model_validate(connector_response)

    @pytest.mark.parametrize(
        ("api_state", "enum_state"),
        [
            pytest.param("RUNNING", ConnectorCurrentState.RUNNING),
            pytest.param("PAUSED", ConnectorCurrentState.PAUSED),
            pytest.param("STOPPED", ConnectorCurrentState.STOPPED),
            pytest.param("FAILED", ConnectorCurrentState.FAILED),
        ],
    )
    async def test_get_connector_status(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        api_state: str,
        enum_state: ConnectorCurrentState,
    ):
        actual_response: dict[str, Any] = {
            "name": CONNECTOR_NAME,
            "connector": {
                "state": api_state,
                "worker_id": "kafka-connect.infrastructure.svc:8083",
            },
            "tasks": [],
            "type": "sink",
        }
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/status",
            headers=HEADERS,
            status_code=httpx.codes.OK,
            json=actual_response,
        )
        status = await connect_wrapper.get_connector_status(CONNECTOR_NAME)
        assert status == ConnectorStatusResponse(
            name=CONNECTOR_NAME,
            connector=ConnectorStatus(
                state=enum_state, worker_id="kafka-connect.infrastructure.svc:8083"
            ),
            tasks=[],
            type=KafkaConnectorType.SINK,
        )

    async def test_pause_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        caplog: pytest.LogCaptureFixture,
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/pause",
            status_code=httpx.codes.ACCEPTED,
        )
        await connect_wrapper.pause_connector(CONNECTOR_NAME)
        assert len(caplog.records) == 1
        assert caplog.records[0].message == f"Connector {CONNECTOR_NAME} paused."
        assert caplog.records[0].levelname == "INFO"

    async def test_pause_error(
        self, connect_wrapper: ConnectWrapper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/pause",
            status_code=httpx.codes.INTERNAL_SERVER_ERROR,
        )
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.pause_connector(CONNECTOR_NAME)

    async def test_resume_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        caplog: pytest.LogCaptureFixture,
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/resume",
            status_code=httpx.codes.ACCEPTED,
        )
        await connect_wrapper.resume_connector(CONNECTOR_NAME)
        assert len(caplog.records) == 1
        assert caplog.records[0].message == f"Connector {CONNECTOR_NAME} resumed."
        assert caplog.records[0].levelname == "INFO"

    async def test_resume_connector_error(
        self, connect_wrapper: ConnectWrapper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/resume",
            status_code=httpx.codes.INTERNAL_SERVER_ERROR,
        )
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.resume_connector(CONNECTOR_NAME)

    async def test_stop_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        caplog: pytest.LogCaptureFixture,
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/stop",
            status_code=httpx.codes.NO_CONTENT,
        )
        await connect_wrapper.stop_connector(CONNECTOR_NAME)
        assert len(caplog.records) == 1
        assert caplog.records[0].message == f"Connector {CONNECTOR_NAME} stopped."
        assert caplog.records[0].levelname == "INFO"

    async def test_stop_connector_error(
        self, connect_wrapper: ConnectWrapper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/stop",
            status_code=httpx.codes.INTERNAL_SERVER_ERROR,
        )
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.stop_connector(CONNECTOR_NAME)

    @patch("httpx.AsyncClient.put")
    async def test_update_connector_request(
        self,
        mock_put: AsyncMock,
        connect_wrapper: ConnectWrapper,
        connector_config: KafkaConnectorConfig,
    ):
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.update_connector_config(connector_config)
        mock_put.assert_called_with(
            f"/connectors/{CONNECTOR_NAME}/config",
            json=connector_config.model_dump(),
        )

    async def test_update_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
        connector_response: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/config",
            headers=HEADERS,
            status_code=httpx.codes.OK,
            json=connector_response,
        )
        with caplog.at_level(logging.INFO):
            actual_response = await connect_wrapper.update_connector_config(
                connector_config
            )
        assert ConnectorResponse.model_validate(connector_response) == actual_response
        assert len(caplog.records) == 1
        assert (
            caplog.records[0].message
            == f"Config for connector {CONNECTOR_NAME} updated."
        )
        assert caplog.records[0].levelname == "INFO"

    async def test_update_create_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
        connector_response: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/config",
            headers=HEADERS,
            status_code=httpx.codes.CREATED,
            json=connector_response,
        )
        with caplog.at_level(logging.INFO):
            actual_response = await connect_wrapper.update_connector_config(
                connector_config
            )
        assert ConnectorResponse.model_validate(connector_response) == actual_response
        assert len(caplog.records) == 1
        assert caplog.records[0].message == f"Connector {CONNECTOR_NAME} created."
        assert caplog.records[0].levelname == "INFO"

    @pytest.mark.usefixtures("mock_sleep")
    async def test_update_connector_retry(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_response: dict[str, Any],
        connector_config: KafkaConnectorConfig,
        caplog: pytest.LogCaptureFixture,
    ):
        ENDPOINT = f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/config"
        httpx_mock.add_response(
            method="PUT",
            url=ENDPOINT,
            headers=HEADERS,
            status_code=httpx.codes.CONFLICT,
            json={},
        )
        httpx_mock.add_response(
            method="PUT",
            url=ENDPOINT,
            headers=HEADERS,
            json=connector_response,
        )

        with caplog.at_level(logging.INFO):
            await connect_wrapper.update_connector_config(connector_config)

        assert len(caplog.records) == 2
        assert (
            caplog.records[0].message
            == "Rebalancing in progress while updating a connector... Retrying..."
        )
        assert caplog.records[0].levelname == "WARNING"
        assert (
            caplog.records[1].message == "Config for connector test-connector updated."
        )
        assert caplog.records[1].levelname == "INFO"

    async def test_delete_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        caplog: pytest.LogCaptureFixture,
    ):
        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            status_code=httpx.codes.NO_CONTENT,
        )
        await connect_wrapper.delete_connector(CONNECTOR_NAME)
        assert len(caplog.records) == 1
        assert caplog.records[0].message == f"Connector {CONNECTOR_NAME} deleted."
        assert caplog.records[0].levelname == "INFO"

    async def test_delete_connector_not_found(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            status_code=httpx.codes.NOT_FOUND,
            json={
                "error_code": httpx.codes.NOT_FOUND.value,
                "message": f"Connector {CONNECTOR_NAME} not found",
            },
        )
        with pytest.raises(ConnectorNotFoundException):
            await connect_wrapper.delete_connector(CONNECTOR_NAME)

    @pytest.mark.usefixtures("mock_sleep")
    async def test_delete_connector_retry(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        caplog: pytest.LogCaptureFixture,
    ):
        ENDPOINT = f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}"
        httpx_mock.add_response(
            method="DELETE",
            url=ENDPOINT,
            headers=HEADERS,
            status_code=httpx.codes.CONFLICT,
            json={},
        )
        httpx_mock.add_response(
            method="DELETE",
            url=ENDPOINT,
            status_code=httpx.codes.NO_CONTENT,
        )

        with caplog.at_level(logging.INFO):
            await connect_wrapper.delete_connector(CONNECTOR_NAME)

        assert len(caplog.records) == 2
        assert (
            caplog.records[0].message
            == "Rebalancing in progress while deleting a connector... Retrying..."
        )
        assert caplog.records[0].levelname == "WARNING"
        assert caplog.records[1].message == "Connector test-connector deleted."
        assert caplog.records[1].levelname == "INFO"

    @pytest.fixture()
    def file_stream_connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig.model_validate(
            {
                "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
                "name": "FileStreamSinkConnector",
                "tasks.max": "1",
                "topics": "test-topic",
            }
        )

    @patch("httpx.AsyncClient.put")
    async def test_validate_connector_config_request(
        self,
        mock_put: AsyncMock,
        connect_wrapper: ConnectWrapper,
        file_stream_connector_config: KafkaConnectorConfig,
    ):
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.validate_connector_config(
                file_stream_connector_config
            )
        mock_put.assert_called_with(
            f"/connector-plugins/{file_stream_connector_config.name}/config/validate",
            json=file_stream_connector_config.model_dump(),
        )

    async def test_validate_connector_config(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        file_stream_connector_config: KafkaConnectorConfig,
    ):
        content = await Path(
            RESOURCES_PATH / "connect_validation_response.json",
        ).read_text()
        actual_response = json.loads(content)

        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connector-plugins/{file_stream_connector_config.name}/config/validate",
            headers=HEADERS,
            json=actual_response,
        )

        errors = await connect_wrapper.validate_connector_config(
            file_stream_connector_config
        )
        assert errors == [
            "Found error for field file: Missing required configuration 'file' which has no default value."
        ]
