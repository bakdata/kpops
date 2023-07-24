import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from pytest_httpx import HTTPXMock

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers.kafka_connect.connect_wrapper import ConnectWrapper
from kpops.component_handlers.kafka_connect.exception import (
    ConnectorNotFoundException,
    KafkaConnectError,
)
from kpops.component_handlers.kafka_connect.model import (
    KafkaConnectConfig,
    KafkaConnectResponse,
)
from kpops.component_handlers.kafka_connect.timeout import timeout

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

HOST = "http://localhost:8083"
DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestConnectorApiWrapper:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self):
        config = PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            kafka_connect_host=HOST,
        )
        self.connect_wrapper = ConnectWrapper(host=config.kafka_connect_host)

    def test_should_through_exception_when_host_is_not_set(self):
        config = PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            kafka_connect_host=None,
        )
        with pytest.raises(RuntimeError) as run_time_error:
            ConnectWrapper(host=config.kafka_connect_host)
        assert (
            str(run_time_error.value)
            == "The Kafka Connect host is not set. Please set the host in the config."
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.post")
    async def test_should_create_post_requests_for_given_connector_configuration(
        self, mock_post: MagicMock
    ):
        configs = {
            "batch.size": "50",
            "value.converter": "com.bakdata.kafka.LargeMessageConverter",
            "connection.username": "fake-user",
            "value.converter.large.message.converter": "io.confluent.connect.avro.AvroConverter",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
        }

        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.create_connector(
                "test-connector", kafka_connect_config=KafkaConnectConfig(**configs)
            )

        mock_post.assert_called_with(
            url=f"{HOST}/connectors",
            headers=HEADERS,
            json={
                "name": "test-connector",
                "config": KafkaConnectConfig(**configs).dict(),
            },
        )

    @pytest.mark.asyncio
    async def test_should_return_correct_response_when_connector_created(
        self, httpx_mock
    ):
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
            method="POST",
            url=f"{HOST}/connectors",
            headers=HEADERS,
            json=actual_response,
            status_code=201,
        )
        expected_response = await self.connect_wrapper.create_connector(
            "test-connector", kafka_connect_config=KafkaConnectConfig()
        )
        assert KafkaConnectResponse(**actual_response) == expected_response

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_connector_exists_exception_when_connector_exists(
        self, log_warning: MagicMock, httpx_mock: HTTPXMock
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"{HOST}/connectors",
            json={},
            status_code=409,
        )

        async def create_connector_locally():
            await self.connect_wrapper.create_connector(
                "test-name", KafkaConnectConfig()
            )

        await timeout(
            create_connector_locally(),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while creating a connector... Retrying..."
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.get")
    async def test_should_create_correct_get_connector_request(
        self, mock_get: MagicMock
    ):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.get_connector(connector_name)

        mock_get.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    @pytest.mark.asyncio
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
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json=actual_response,
            status_code=200,
        )
        expected_response = await self.connect_wrapper.get_connector(connector_name)
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} exists.")

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_raise_connector_not_found_when_getting_connector(
        self, log_info: MagicMock, httpx_mock: HTTPXMock
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="GET",
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=404,
        )
        with pytest.raises(ConnectorNotFoundException):
            await self.connect_wrapper.get_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @pytest.mark.asyncio
    async def test_should_raise_connector_name_do_not_match(self):
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
            "name": "OtherWrongName",
        }
        with pytest.raises(ValueError) as value_error:
            await self.connect_wrapper.validate_connector_config(
                "FileStreamSinkConnector",
                kafka_connect_config=KafkaConnectConfig(**configs),
            )

        assert (
            str(value_error.value)
            == "Connector name should be the same as component name"
        )

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_getting_connector(
        self, log_warning: MagicMock, httpx_mock: HTTPXMock
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="GET",
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=409,
        )

        async def get_connector_locally():
            return await self.connect_wrapper.get_connector(connector_name)

        await timeout(
            get_connector_locally(),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while getting a connector... Retrying..."
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_update_connector_request(
        self, mock_put: MagicMock
    ):
        connector_name = "test-connector"
        configs = {
            "batch.size": "50",
            "value.converter": "com.bakdata.kafka.LargeMessageConverter",
            "connection.username": "fake-user",
            "value.converter.large.message.converter": "io.confluent.connect.avro.AvroConverter",
            "max.buffered.records": "500",
            "connection.password": "fake-password",
            "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
        }
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.update_connector_config(
                connector_name,
                KafkaConnectConfig(**configs),
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}/config",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectConfig(**configs).dict(),
        )

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector(
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
            method="PUT",
            url=f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=200,
        )
        expected_response = await self.connect_wrapper.update_connector_config(
            connector_name, KafkaConnectConfig()
        )
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(
            f"Config for connector {connector_name} updated."
        )

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_return_correct_response_when_update_connector_created(
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
            method="PUT",
            url=f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=201,
        )
        expected_response = await self.connect_wrapper.update_connector_config(
            connector_name, KafkaConnectConfig()
        )
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} created.")

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_connector_exists_exception_when_update_connector(
        self, log_warning: MagicMock, httpx_mock: HTTPXMock
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="PUT",
            url=f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json={},
            status_code=409,
        )

        async def update_connector_locally():
            await self.connect_wrapper.update_connector_config(
                connector_name, KafkaConnectConfig()
            )

        await timeout(
            update_connector_locally(),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while updating a connector... Retrying..."
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.delete")
    async def test_should_create_correct_delete_connector_request(
        self, mock_delete: MagicMock
    ):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.delete_connector(connector_name)

        mock_delete.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
        )

    @pytest.mark.asyncio
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
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json=actual_response,
            status_code=204,
        )
        await self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(f"Connector {connector_name} deleted.")

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    async def test_should_raise_connector_not_found_when_deleting_connector(
        self, log_info: MagicMock, httpx_mock: HTTPXMock
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="DELETE",
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=404,
        )
        with pytest.raises(ConnectorNotFoundException):
            await self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @pytest.mark.asyncio
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    async def test_should_raise_rebalance_in_progress_when_deleting_connector(
        self, log_warning: MagicMock, httpx_mock: HTTPXMock
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="DELETE",
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status_code=409,
        )

        async def delete_connector_locally():
            await self.connect_wrapper.delete_connector(connector_name)

        await timeout(
            delete_connector_locally(),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while deleting a connector... Retrying..."
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_validate_connector_config_request(
        self, mock_put: MagicMock
    ):
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
            "name": "FileStreamSinkConnector",
        }
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.validate_connector_config(
                "FileStreamSinkConnector",
                kafka_connect_config=KafkaConnectConfig(**configs),
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectConfig(**configs).dict(),
        )

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient.put")
    async def test_should_create_correct_validate_connector_config_and_name_gets_added(
        self, mock_put: MagicMock
    ):
        connector_name = "FileStreamSinkConnector"
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
        }
        with pytest.raises(KafkaConnectError):
            await self.connect_wrapper.validate_connector_config(
                connector_name,
                kafka_connect_config=KafkaConnectConfig(**configs),
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connector-plugins/{connector_name}/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectConfig(**{"name": connector_name, **configs}).dict(),
        )

    @pytest.mark.asyncio
    async def test_should_parse_validate_connector_config(self, httpx_mock: HTTPXMock):
        with open(
            DEFAULTS_PATH / "connect_validation_response.json",
        ) as f:
            actual_response = json.load(f)

        httpx_mock.add_response(
            method="PUT",
            url=f"{HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers=HEADERS,
            json=actual_response,
            status_code=200,
        )

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
        }
        errors = await self.connect_wrapper.validate_connector_config(
            "FileStreamSinkConnector",
            kafka_connect_config=KafkaConnectConfig(**configs),
        )

        assert errors == [
            "Found error for field file: Missing required configuration 'file' which has no default value."
        ]
