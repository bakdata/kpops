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
    @pytest_asyncio.fixture(autouse=True)
    def _setup(self):
        config = KpopsConfig()
        self.connect_wrapper = ConnectWrapper(config.kafka_connect)

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig(
            **{  # pyright: ignore[reportArgumentType]
                "connector.class": "com.bakdata.connect.TestConnector",
                "name": "test-connector",
            }
        )

    @pytest.mark.asyncio()
    @patch("httpx.AsyncClient.post")
    async def test_should_create_post_requests_for_given_connector_configuration(
        self, mock_post: AsyncMock
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
            await self.connect_wrapper.create_connector(KafkaConnectorConfig(**configs))  # pyright: ignore[reportArgumentType]

        mock_post.assert_called_with(
            url=f"{DEFAULT_HOST}/connectors",
            headers=HEADERS,
            json={
                "name": "test-connector",
                "config": KafkaConnectorConfig(**configs).model_dump(),  # pyright: ignore[reportArgumentType]
            },
        )

    @pytest.mark.asyncio()
    async def test_should_return_correct_response_when_connector_created(
        self, httpx_mock: HTTPXMock, connector_config: KafkaConnectorConfig
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

        expected_response = await self.connect_wrapper.create_connector(
            connector_config
        )

        assert KafkaConnectResponse(**actual_response) == expected_response

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_connector_exists_exception_when_connector_exists(
        self,
        log_warning: MagicMock,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"{DEFAULT_HOST}/connectors",
            json={},
            status_code=409,
        )

        await timeout(
            self.connect_wrapper.create_connector(connector_config),
            secs=10,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while creating a connector... Retrying..."
        )

    @pytest.mark.asyncio()
    @patch("httpx.AsyncClient.get")
    async def test_should_create_correct_get_connector_request(
        self, mock_get: AsyncMock
    ):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.get_connector(connector_name)

        mock_get.assert_called_with(
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_getting_connector(
        self, log_info: MagicMock, httpx_mock: HTTPXMock
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
        expected_response = await self.connect_wrapper.get_connector(connector_name)
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} exists.")

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_raise_connector_not_found_when_getting_connector(
        self, log_info: MagicMock, httpx_mock: HTTPXMock
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
            await self.connect_wrapper.get_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_getting_connector(
        self, log_warning: MagicMock, httpx_mock: HTTPXMock
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
            self.connect_wrapper.get_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while getting a connector... Retrying..."
        )

    @pytest.mark.asyncio()
    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_update_connector_request(
        self, mock_put: AsyncMock
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
            await self.connect_wrapper.update_connector_config(
                KafkaConnectorConfig(**configs)  # pyright: ignore[reportArgumentType]
            )

        mock_put.assert_called_with(
            url=f"{DEFAULT_HOST}/connectors/{connector_name}/config",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectorConfig(**configs).model_dump(),  # pyright: ignore[reportArgumentType]
        )

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector(
        self,
        log_info: MagicMock,
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

        expected_response = await self.connect_wrapper.update_connector_config(
            connector_config
        )
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(
            f"Config for connector {connector_name} updated."
        )

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector_created(
        self,
        log_info: MagicMock,
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
        expected_response = await self.connect_wrapper.update_connector_config(
            connector_config
        )
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} created.")

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_connector_exists_exception_when_update_connector(
        self,
        log_warning: MagicMock,
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
            self.connect_wrapper.update_connector_config(connector_config),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while updating a connector... Retrying..."
        )

    @pytest.mark.asyncio()
    @patch("httpx.AsyncClient.delete")
    async def test_should_create_correct_delete_connector_request(
        self, mock_delete: AsyncMock
    ):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.delete_connector(connector_name)

        mock_delete.assert_called_with(
            url=f"{DEFAULT_HOST}/connectors/{connector_name}",
            headers=HEADERS,
        )

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_deleting_connector(
        self, log_info: MagicMock, httpx_mock: HTTPXMock
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
        await self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(f"Connector {connector_name} deleted.")

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_raise_connector_not_found_when_deleting_connector(
        self, log_info: MagicMock, httpx_mock: HTTPXMock
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
            await self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @pytest.mark.asyncio()
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_deleting_connector(
        self, log_warning: MagicMock, httpx_mock: HTTPXMock
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
            self.connect_wrapper.delete_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while deleting a connector... Retrying..."
        )

    @pytest.mark.asyncio()
    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_validate_connector_config_request(
        self, mock_put: AsyncMock
    ):
        connector_config = KafkaConnectorConfig(
            **{  # pyright: ignore[reportArgumentType]
                "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
                "name": "FileStreamSinkConnector",
                "tasks.max": "1",
                "topics": "test-topic",
            }
        )
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.validate_connector_config(connector_config)

        mock_put.assert_called_with(
            url=f"{DEFAULT_HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=connector_config.model_dump(),
        )

    @pytest.mark.asyncio()
    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_validate_connector_config_and_name_gets_added(
        self, mock_put: AsyncMock
    ):
        connector_name = "FileStreamSinkConnector"
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": connector_name,
            "tasks.max": "1",
            "topics": "test-topic",
        }
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.validate_connector_config(
                KafkaConnectorConfig(**configs)  # pyright: ignore[reportArgumentType]
            )

        mock_put.assert_called_with(
            url=f"{DEFAULT_HOST}/connector-plugins/{connector_name}/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectorConfig(
                **{"name": connector_name, **configs}  # pyright: ignore[reportArgumentType]
            ).model_dump(),
        )

    @pytest.mark.asyncio()
    async def test_should_parse_validate_connector_config(self, httpx_mock: HTTPXMock):
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
        errors = await self.connect_wrapper.validate_connector_config(
            KafkaConnectorConfig(**configs)  # pyright: ignore[reportArgumentType]
        )

        assert errors == [
            "Found error for field file: Missing required configuration 'file' which has no default value."
        ]
