import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_httpx import HTTPXMock

from kpops.cli.pipeline_config import PipelineConfig
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

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

HOST = "http://localhost:8083"
DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestConnectorApiWrapper:
    @pytest.fixture(autouse=True)
    def _setup(self):
        config = PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            kafka_connect_host=HOST,
        )
        self.connect_wrapper = ConnectWrapper(host=config.kafka_connect_host)

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig(
            **{
                "connector.class": "com.bakdata.connect.TestConnector",
                "name": "test-connector",
            }
        )

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

    @patch("httpx.post")
    def test_should_create_post_requests_for_given_connector_configuration(
        self, mock_post: MagicMock
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
            self.connect_wrapper.create_connector(KafkaConnectorConfig(**configs))

        mock_post.assert_called_with(
            url=f"{HOST}/connectors",
            headers=HEADERS,
            json={
                "name": "test-connector",
                "config": KafkaConnectorConfig(**configs).model_dump(),
            },
        )

    def test_should_return_correct_response_when_connector_created(
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
            url=f"{HOST}/connectors",
            headers=HEADERS,
            json=actual_response,
            status_code=201,
        )
        expected_response = self.connect_wrapper.create_connector(connector_config)
        assert KafkaConnectResponse(**actual_response) == expected_response

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_connector_exists_exception_when_connector_exists(
        self,
        log_warning: MagicMock,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        httpx_mock.add_response(
            method="POST",
            url=f"{HOST}/connectors",
            json={},
            status_code=409,
        )

        timeout(
            lambda: self.connect_wrapper.create_connector(connector_config),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while creating a connector... Retrying..."
        )

    @patch("httpx.get")
    def test_should_create_correct_get_connector_request(self, mock_get: MagicMock):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            self.connect_wrapper.get_connector(connector_name)

        mock_get.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    @pytest.mark.flaky(reruns=5, condition=sys.platform.startswith("win32"))
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_getting_connector(
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
        expected_response = self.connect_wrapper.get_connector(connector_name)
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} exists.")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_raise_connector_not_found_when_getting_connector(
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
            self.connect_wrapper.get_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_rebalance_in_progress_when_getting_connector(
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

        timeout(
            lambda: self.connect_wrapper.get_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while getting a connector... Retrying..."
        )

    @patch("httpx.put")
    def test_should_create_correct_update_connector_request(self, mock_put: MagicMock):
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
            self.connect_wrapper.update_connector_config(
                KafkaConnectorConfig(**configs)
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}/config",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectorConfig(**configs).model_dump(),
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_update_connector(
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
            url=f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=200,
        )
        expected_response = self.connect_wrapper.update_connector_config(
            connector_config
        )
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(
            f"Config for connector {connector_name} updated."
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_update_connector_created(
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
            url=f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status_code=201,
        )
        expected_response = self.connect_wrapper.update_connector_config(
            connector_config
        )
        assert KafkaConnectResponse(**actual_response) == expected_response
        log_info.assert_called_once_with(f"Connector {connector_name} created.")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_connector_exists_exception_when_update_connector(
        self,
        log_warning: MagicMock,
        httpx_mock: HTTPXMock,
        connector_config: KafkaConnectorConfig,
    ):
        connector_name = "test-connector"

        httpx_mock.add_response(
            method="PUT",
            url=f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json={},
            status_code=409,
        )

        timeout(
            lambda: self.connect_wrapper.update_connector_config(connector_config),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while updating a connector... Retrying..."
        )

    @patch("httpx.delete")
    def test_should_create_correct_delete_connector_request(
        self, mock_delete: MagicMock
    ):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            self.connect_wrapper.delete_connector(connector_name)

        mock_delete.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_deleting_connector(
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
        self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(f"Connector {connector_name} deleted.")

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_raise_connector_not_found_when_deleting_connector(
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
            self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_rebalance_in_progress_when_deleting_connector(
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

        timeout(
            lambda: self.connect_wrapper.delete_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while deleting a connector... Retrying..."
        )

    @patch("httpx.put")
    def test_should_create_correct_validate_connector_config_request(
        self, mock_put: MagicMock
    ):
        connector_config = KafkaConnectorConfig(
            **{
                "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
                "name": "FileStreamSinkConnector",
                "tasks.max": "1",
                "topics": "test-topic",
            }
        )
        with pytest.raises(KafkaConnectError):
            self.connect_wrapper.validate_connector_config(connector_config)

        mock_put.assert_called_with(
            url=f"{HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=connector_config.model_dump(),
        )

    @patch("httpx.put")
    def test_should_create_correct_validate_connector_config_and_name_gets_added(
        self, mock_put: MagicMock
    ):
        connector_name = "FileStreamSinkConnector"
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "name": connector_name,
            "tasks.max": "1",
            "topics": "test-topic",
        }
        with pytest.raises(KafkaConnectError):
            self.connect_wrapper.validate_connector_config(
                KafkaConnectorConfig(**configs)
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connector-plugins/{connector_name}/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectorConfig(**{"name": connector_name, **configs}).model_dump(),
        )

    def test_should_parse_validate_connector_config(self, httpx_mock: HTTPXMock):
        with Path(
            DEFAULTS_PATH / "connect_validation_response.json",
        ).open() as f:
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
            "name": "FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
        }
        errors = self.connect_wrapper.validate_connector_config(
            KafkaConnectorConfig(**configs)
        )

        assert errors == [
            "Found error for field file: Missing required configuration 'file' which has no default value."
        ]
