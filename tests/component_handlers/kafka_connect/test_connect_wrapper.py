import json
import sys
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from anyio import Path
from pytest_httpx import HTTPXMock

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
from kpops.component_handlers.kafka_connect.timeout import timeout
from kpops.config import KpopsConfig
from tests.component_handlers.kafka_connect import RESOURCES_PATH

DEFAULT_HOST = "http://localhost:8083"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}
CONNECTOR_NAME = "test-connector"


class TestConnectorApiWrapper:
    @pytest_asyncio.fixture()
    def connect_wrapper(self) -> ConnectWrapper:
        config = KpopsConfig.model_validate({})
        return ConnectWrapper(config.kafka_connect)

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig.model_validate(
            {
                "connector.class": "com.bakdata.connect.TestConnector",
                "name": CONNECTOR_NAME,
            }
        )

    def test_convert_config_values_to_str(self):
        # all values should be converted to strings
        assert KafkaConnectorConfig.model_validate(
            {
                "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
                "name": CONNECTOR_NAME,
                "batch.size": 50,
                "max.buffered.records": 500,
                "connection.password": "fake-password",
                "store.kafka.keys": True,
                "receive.buffer.bytes": -1,
                "topic.tracking.allow.reset": False,
            }
        ).model_dump() == {
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "name": CONNECTOR_NAME,
            "batch.size": "50",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
            "store.kafka.keys": "true",
            "receive.buffer.bytes": "-1",
            "topic.tracking.allow.reset": "false",
        }

    @patch("httpx.AsyncClient.post")
    async def test_create(
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
    async def test_create_with_initial_state(
        self, mock_post: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        configs = {
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "name": CONNECTOR_NAME,
            "batch.size": "50",
            "value.converter": "com.bakdata.kafka.LargeMessageConverter",
            "connection.username": "fake-user",
            "value.converter.large.message.converter": "io.confluent.connect.avro.AvroConverter",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
        }

        with pytest.raises(KafkaConnectError):
            await connect_wrapper.create_connector(
                KafkaConnectorConfig.model_validate(configs), ConnectorNewState.RUNNING
            )

        mock_post.assert_called_with(
            "/connectors",
            json={
                "name": CONNECTOR_NAME,
                "config": configs,
                "initial_state": "RUNNING",
            },
        )

    async def test_should_return_correct_response_when_connector_created(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        actual_response = {
            "name": "hdfs-sink-connector",
            "type": "sink",
            "config": {
                "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
                "name": CONNECTOR_NAME,
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
        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/connectors",
            headers=HEADERS,
            json=actual_response,
            status_code=httpx.codes.CREATED,
        )

        expected_response = await connect_wrapper.create_connector(
            connector_config, ConnectorNewState.RUNNING
        )

        assert ConnectorResponse.model_validate(actual_response) == expected_response

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_connector_exists_exception_when_connector_exists(
        self,
        log_warning: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/connectors",
            json={},
            status_code=httpx.codes.CONFLICT,
            is_reusable=True,
        )

        await timeout(
            connect_wrapper.create_connector(
                connector_config, ConnectorNewState.RUNNING
            ),
            secs=10,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while creating a connector... Retrying..."
        )

    @patch("httpx.AsyncClient.get")
    async def test_should_create_correct_get_connector_request(
        self, mock_get: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.get_connector(CONNECTOR_NAME)

        mock_get.assert_called_with(f"/connectors/{CONNECTOR_NAME}")

    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    async def test_should_return_correct_response_when_getting_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        actual_response = {
            "name": "hdfs-sink-connector",
            "type": "sink",
            "config": {
                "name": "hdfs-sink-connector",
                "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
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
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            json=actual_response,
            status_code=httpx.codes.OK,
        )
        expected_response = await connect_wrapper.get_connector(CONNECTOR_NAME)
        assert ConnectorResponse.model_validate(actual_response) == expected_response

    async def test_should_raise_connector_not_found_when_getting_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            json={},
            status_code=httpx.codes.NOT_FOUND,
        )
        with pytest.raises(ConnectorNotFoundException):
            await connect_wrapper.get_connector(CONNECTOR_NAME)

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_getting_connector(
        self,
        log_warning: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            json={},
            status_code=httpx.codes.CONFLICT,
        )

        await timeout(
            connect_wrapper.get_connector(CONNECTOR_NAME),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while getting a connector... Retrying..."
        )

    async def test_pause(
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
        assert caplog.messages == [f"Connector {CONNECTOR_NAME} paused."]

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

    async def test_resume(
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
        assert caplog.messages == [f"Connector {CONNECTOR_NAME} resumed."]

    async def test_resume_error(
        self, connect_wrapper: ConnectWrapper, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/resume",
            status_code=httpx.codes.INTERNAL_SERVER_ERROR,
        )
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.resume_connector(CONNECTOR_NAME)

    async def test_stop(
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
        assert caplog.messages == [f"Connector {CONNECTOR_NAME} stopped."]

    async def test_stop_error(
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
    async def test_should_create_correct_update_connector_request(
        self, mock_put: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        configs = {
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "name": CONNECTOR_NAME,
            "batch.size": "50",
            "value.converter": "com.bakdata.kafka.LargeMessageConverter",
            "connection.username": "fake-user",
            "value.converter.large.message.converter": "io.confluent.connect.avro.AvroConverter",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
        }
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.update_connector_config(
                KafkaConnectorConfig.model_validate(configs)
            )

        mock_put.assert_called_with(
            f"/connectors/{CONNECTOR_NAME}/config",
            json=configs,
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        actual_response = {
            "name": "hdfs-sink-connector",
            "type": "sink",
            "config": {
                "name": "hdfs-sink-connector",
                "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
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
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=httpx.codes.OK,
        )

        expected_response = await connect_wrapper.update_connector_config(
            connector_config
        )
        assert ConnectorResponse.model_validate(actual_response) == expected_response
        log_info.assert_called_once_with(
            f"Config for connector {CONNECTOR_NAME} updated."
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector_created(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        actual_response = {
            "name": "hdfs-sink-connector",
            "type": "sink",
            "config": {
                "name": "hdfs-sink-connector",
                "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
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
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=httpx.codes.CREATED,
        )
        expected_response = await connect_wrapper.update_connector_config(
            connector_config
        )
        assert ConnectorResponse.model_validate(actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {CONNECTOR_NAME} created.")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_connector_exists_exception_when_update_connector(
        self,
        log_warning: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}/config",
            headers=HEADERS,
            json={},
            status_code=httpx.codes.CONFLICT,
        )

        await timeout(
            connect_wrapper.update_connector_config(connector_config),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while updating a connector... Retrying..."
        )

    @patch("httpx.AsyncClient.delete")
    async def test_should_create_correct_delete_connector_request(
        self, mock_delete: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.delete_connector(CONNECTOR_NAME)

        mock_delete.assert_called_with(f"/connectors/{CONNECTOR_NAME}")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_deleting_connector(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        actual_response = {
            "name": "hdfs-sink-connector",
            "config": {
                "name": "hdfs-sink-connector",
                "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
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
        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            json=actual_response,
            status_code=httpx.codes.NO_CONTENT,
        )
        await connect_wrapper.delete_connector(CONNECTOR_NAME)

        log_info.assert_called_once_with(f"Connector {CONNECTOR_NAME} deleted.")

    async def test_should_raise_connector_not_found_when_deleting_connector(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            json={},
            status_code=httpx.codes.NOT_FOUND,
        )
        with pytest.raises(ConnectorNotFoundException):
            await connect_wrapper.delete_connector(CONNECTOR_NAME)

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_deleting_connector(
        self,
        log_warning: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/connectors/{CONNECTOR_NAME}",
            headers=HEADERS,
            json={},
            status_code=httpx.codes.CONFLICT,
        )

        await timeout(
            connect_wrapper.delete_connector(CONNECTOR_NAME),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while deleting a connector... Retrying..."
        )

    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_validate_connector_config_request(
        self, mock_put: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        connector_name = "FileStreamSinkConnector"
        config = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": connector_name,
            "tasks.max": "1",
            "topics": "test-topic",
        }
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.validate_connector_config(
                KafkaConnectorConfig.model_validate(config)
            )

        mock_put.assert_called_with(
            f"/connector-plugins/{connector_name}/config/validate",
            json=config,
        )

    @pytest.mark.parametrize(
        ("api_state", "enum_state"),
        [
            pytest.param("RUNNING", ConnectorCurrentState.RUNNING),
            pytest.param("PAUSED", ConnectorCurrentState.PAUSED),
            pytest.param("STOPPED", ConnectorCurrentState.STOPPED),
            pytest.param("FAILED", ConnectorCurrentState.FAILED),
        ],
    )
    async def test_should_parse_connector_status(
        self,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        api_state: str,
        enum_state: ConnectorCurrentState,
    ):
        connector_name = "hdfs-sink-connector"
        actual_response: dict[str, Any] = {
            "name": connector_name,
            "connector": {
                "state": api_state,
                "worker_id": "kafka-connect.infrastructure.svc:8083",
            },
            "tasks": [],
            "type": "sink",
        }
        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{connector_name}/status",
            headers=HEADERS,
            json=actual_response,
            status_code=httpx.codes.OK,
        )
        status = await connect_wrapper.get_connector_status(connector_name)
        assert status == ConnectorStatusResponse(
            name=connector_name,
            connector=ConnectorStatus(
                state=enum_state, worker_id="kafka-connect.infrastructure.svc:8083"
            ),
            tasks=[],
            type=KafkaConnectorType.SINK,
        )

    async def test_should_parse_validate_connector_config(
        self, connect_wrapper: ConnectWrapper, httpx_mock: HTTPXMock
    ):
        content = await Path(
            RESOURCES_PATH / "connect_validation_response.json",
        ).read_text()
        actual_response = json.loads(content)

        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers=HEADERS,
            json=actual_response,
            status_code=httpx.codes.OK,
        )

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": "FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
        }
        errors = await connect_wrapper.validate_connector_config(
            KafkaConnectorConfig.model_validate(configs)
        )

        assert errors == [
            "Found error for field file: Missing required configuration 'file' which has no default value."
        ]
