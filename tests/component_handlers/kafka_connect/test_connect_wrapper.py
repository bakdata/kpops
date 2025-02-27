import json
import sys
from unittest.mock import AsyncMock, MagicMock, patch

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
    KafkaConnectorConfig,
    KafkaConnectResponse,
)
from kpops.component_handlers.kafka_connect.timeout import timeout
from kpops.config import KpopsConfig
from tests.component_handlers.kafka_connect import RESOURCES_PATH

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

DEFAULT_HOST = "http://localhost:8083"


class TestConnectorApiWrapper:
    @pytest_asyncio.fixture()
    def connect_wrapper(self) -> ConnectWrapper:
        config = KpopsConfig()  # pyright: ignore[reportCallIssue]
        return ConnectWrapper(config.kafka_connect)

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig.model_validate(
            {
                "connector.class": "com.bakdata.connect.TestConnector",
                "name": "test-connector",
            }
        )

    def test_convert_config_values_to_str(self):
        # all values should be converted to strings
        assert KafkaConnectorConfig.model_validate(
            {
                "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
                "name": "test-connector",
                "batch.size": 50,
                "max.buffered.records": 500,
                "connection.password": "fake-password",
                "store.kafka.keys": True,
                "receive.buffer.bytes": -1,
                "topic.tracking.allow.reset": False,
            }
        ).model_dump() == {
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "name": "test-connector",
            "batch.size": "50",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
            "store.kafka.keys": "true",
            "receive.buffer.bytes": "-1",
            "topic.tracking.allow.reset": "false",
        }

    @patch("httpx.AsyncClient.post")
    async def test_should_create_post_requests_for_given_connector_configuration(
        self, mock_post: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        configs = {
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "name": "test-connector",
            "batch.size": "50",
            "value.converter": "com.bakdata.kafka.LargeMessageConverter",
            "connection.username": "fake-user",
            "value.converter.large.message.converter": "io.confluent.connect.avro.AvroConverter",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
        }

        with pytest.raises(KafkaConnectError):
            await connect_wrapper.create_connector(
                KafkaConnectorConfig.model_validate(configs)
            )

        mock_post.assert_called_with(
            url=f"{DEFAULT_HOST}/connectors",
            headers=HEADERS,
            json={
                "name": "test-connector",
                "config": KafkaConnectorConfig.model_validate(configs).model_dump(),
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
            "config": {
                "connector.class": "io.confluent.connect.hdfs.HdfsSinkConnector",
                "name": "test-connector",
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
            status_code=201,
        )

        expected_response = await connect_wrapper.create_connector(connector_config)

        assert KafkaConnectResponse.model_validate(actual_response) == expected_response

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
            status_code=409,
            is_reusable=True,
        )

        await timeout(
            connect_wrapper.create_connector(connector_config),
            secs=10,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while creating a connector... Retrying..."
        )

    @patch("httpx.AsyncClient.get")
    async def test_should_create_correct_get_connector_request(
        self, mock_get: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.get_connector(connector_name)

        mock_get.assert_called_with(
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_getting_connector(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        connector_name = "test-connector"

        actual_response = {
            "name": "hdfs-sink-connector",
            "config": {
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
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json=actual_response,
            status_code=200,
        )
        expected_response = await connect_wrapper.get_connector(connector_name)
        assert KafkaConnectResponse.model_validate(actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} exists.")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_raise_connector_not_found_when_getting_connector(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=404,
        )
        with pytest.raises(ConnectorNotFoundException):
            await connect_wrapper.get_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_getting_connector(
        self,
        log_warning: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="GET",
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=409,
        )

        await timeout(
            connect_wrapper.get_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while getting a connector... Retrying..."
        )

    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_update_connector_request(
        self, mock_put: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        connector_name = "test-connector"
        configs = {
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
            "name": connector_name,
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
            url=f"{DEFAULT_HOST}/connectors/{connector_name}/config",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectorConfig.model_validate(configs).model_dump(),
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector_name = "test-connector"

        actual_response = {
            "name": "hdfs-sink-connector",
            "config": {
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
            url=f"{DEFAULT_HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=200,
        )

        expected_response = await connect_wrapper.update_connector_config(
            connector_config
        )
        assert KafkaConnectResponse.model_validate(actual_response) == expected_response
        log_info.assert_called_once_with(
            f"Config for connector {connector_name} updated."
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector_created(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector_name = "test-connector"

        actual_response = {
            "name": "hdfs-sink-connector",
            "config": {
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
            url=f"{DEFAULT_HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=201,
        )
        expected_response = await connect_wrapper.update_connector_config(
            connector_config
        )
        assert KafkaConnectResponse.model_validate(actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} created.")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_connector_exists_exception_when_update_connector(
        self,
        log_warning: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="PUT",
            url=f"{DEFAULT_HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json={},
            status_code=409,
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
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.delete_connector(connector_name)

        mock_delete.assert_called_with(
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_deleting_connector(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        connector_name = "test-connector"

        actual_response = {
            "name": "hdfs-sink-connector",
            "config": {
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
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json=actual_response,
            status_code=204,
        )
        await connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(f"Connector {connector_name} deleted.")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_raise_connector_not_found_when_deleting_connector(
        self,
        log_info: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=404,
        )
        with pytest.raises(ConnectorNotFoundException):
            await connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_deleting_connector(
        self,
        log_warning: MagicMock,
        connect_wrapper: ConnectWrapper,
        httpx_mock: HTTPXMock,
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="DELETE",
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=409,
        )

        await timeout(
            connect_wrapper.delete_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while deleting a connector... Retrying..."
        )

    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_validate_connector_config_request(
        self, mock_put: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        connector_config = KafkaConnectorConfig.model_validate(
            {
                "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
                "name": "FileStreamSinkConnector",
                "tasks.max": "1",
                "topics": "test-topic",
            }
        )
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.validate_connector_config(connector_config)

        mock_put.assert_called_with(
            url=f"{DEFAULT_HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=connector_config.model_dump(),
        )

    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_validate_connector_config_and_name_gets_added(
        self, mock_put: AsyncMock, connect_wrapper: ConnectWrapper
    ):
        connector_name = "FileStreamSinkConnector"
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": connector_name,
            "tasks.max": "1",
            "topics": "test-topic",
        }
        with pytest.raises(KafkaConnectError):
            await connect_wrapper.validate_connector_config(
                KafkaConnectorConfig.model_validate(configs)
            )

        mock_put.assert_called_with(
            url=f"{DEFAULT_HOST}/connector-plugins/{connector_name}/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectorConfig.model_validate(
                {"name": connector_name, **configs}
            ).model_dump(),
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
            status_code=200,
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
