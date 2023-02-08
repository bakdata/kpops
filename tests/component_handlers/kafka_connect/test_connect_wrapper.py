import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import responses

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


class TestConnectorApiWrapper(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
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

    @patch("requests.post")
    def test_should_create_post_requests_for_given_connector_configuration(
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
            self.connect_wrapper.create_connector(
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

    @responses.activate
    def test_should_return_correct_response_when_connector_created(self):
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
        responses.add(
            responses.POST,
            f"{HOST}/connectors",
            headers=HEADERS,
            json=actual_response,
            status=201,
        )
        expected_response = self.connect_wrapper.create_connector(
            "test-connector", kafka_connect_config=KafkaConnectConfig()
        )
        self.assertEqual(KafkaConnectResponse(**actual_response), expected_response)

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_connector_exists_exception_when_connector_exists(
        self, log_warning: MagicMock
    ):
        responses.add(
            responses.POST,
            f"{HOST}/connectors",
            json={},
            status=409,
        )

        timeout(
            lambda: self.connect_wrapper.create_connector(
                "test-name", KafkaConnectConfig()
            ),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while creating a connector... Retrying..."
        )

    @patch("requests.get")
    def test_should_create_correct_get_connector_request(self, mock_get: MagicMock):
        connector_name = "test-connector"
        with pytest.raises(KafkaConnectError):
            self.connect_wrapper.get_connector(connector_name)

        mock_get.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_getting_connector(
        self, log_info: MagicMock
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
        responses.add(
            responses.GET,
            f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json=actual_response,
            status=200,
        )
        expected_response = self.connect_wrapper.get_connector(connector_name)
        self.assertEqual(KafkaConnectResponse(**actual_response), expected_response)
        log_info.assert_called_once_with(f"Connector {connector_name} exists.")

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_raise_connector_not_found_when_getting_connector(
        self, log_info: MagicMock
    ):
        connector_name = "test-connector"

        responses.add(
            responses.GET,
            f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status=404,
        )
        with pytest.raises(ConnectorNotFoundException):
            self.connect_wrapper.get_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    def test_should_raise_connector_name_do_not_match(self):
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
            "name": "OtherWrongName",
        }
        with pytest.raises(ValueError) as value_error:
            self.connect_wrapper.validate_connector_config(
                "FileStreamSinkConnector",
                kafka_connect_config=KafkaConnectConfig(**configs),
            )

        assert (
            str(value_error.value)
            == "Kafka Connect config should be the same as component name"
        )

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_rebalance_in_progress_when_getting_connector(
        self, log_warning: MagicMock
    ):
        connector_name = "test-connector"

        responses.add(
            responses.GET,
            f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status=409,
        )

        timeout(
            lambda: self.connect_wrapper.get_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while getting a connector... Retrying..."
        )

    @patch("requests.put")
    def test_should_create_correct_update_connector_request(self, mock_put: MagicMock):
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
            self.connect_wrapper.update_connector_config(
                connector_name,
                KafkaConnectConfig(**configs),
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connectors/{connector_name}/config",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectConfig(**configs).dict(),
        )

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_update_connector(
        self, log_info: MagicMock
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
        responses.add(
            responses.PUT,
            f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status=200,
        )
        expected_response = self.connect_wrapper.update_connector_config(
            connector_name, KafkaConnectConfig()
        )
        self.assertEqual(KafkaConnectResponse(**actual_response), expected_response)
        log_info.assert_called_once_with(
            f"Config for connector {connector_name} updated."
        )

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_update_connector_created(
        self, log_info: MagicMock
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
        responses.add(
            responses.PUT,
            f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json=actual_response,
            status=201,
        )
        expected_response = self.connect_wrapper.update_connector_config(
            connector_name, KafkaConnectConfig()
        )
        self.assertEqual(KafkaConnectResponse(**actual_response), expected_response)
        log_info.assert_called_once_with(f"Connector {connector_name} created.")

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_connector_exists_exception_when_update_connector(
        self, log_warning: MagicMock
    ):
        connector_name = "test-connector"

        responses.add(
            responses.PUT,
            f"{HOST}/connectors/{connector_name}/config",
            headers=HEADERS,
            json={},
            status=409,
        )

        timeout(
            lambda: self.connect_wrapper.update_connector_config(
                connector_name, KafkaConnectConfig()
            ),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while updating a connector... Retrying..."
        )

    @patch("requests.delete")
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

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_return_correct_response_when_deleting_connector(
        self, log_info: MagicMock
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
        responses.add(
            responses.DELETE,
            f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json=actual_response,
            status=204,
        )
        self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(f"Connector {connector_name} deleted.")

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.info")
    def test_should_raise_connector_not_found_when_deleting_connector(
        self, log_info: MagicMock
    ):
        connector_name = "test-connector"

        responses.add(
            responses.DELETE,
            f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status=404,
        )
        with pytest.raises(ConnectorNotFoundException):
            self.connect_wrapper.delete_connector(connector_name)

        log_info.assert_called_once_with(
            f"The named connector {connector_name} does not exists."
        )

    @responses.activate
    @patch("kpops.component_handlers.kafka_connect.connect_wrapper.log.warning")
    def test_should_raise_rebalance_in_progress_when_deleting_connector(
        self, log_warning: MagicMock
    ):
        connector_name = "test-connector"

        responses.add(
            responses.DELETE,
            f"{HOST}/connectors/{connector_name}",
            headers=HEADERS,
            json={},
            status=409,
        )

        timeout(
            lambda: self.connect_wrapper.delete_connector(connector_name),
            secs=1,
        )

        log_warning.assert_called_with(
            "Rebalancing in progress while deleting a connector... Retrying..."
        )

    @patch("requests.put")
    def test_should_create_correct_validate_connector_config_request(
        self, mock_put: MagicMock
    ):
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
            "name": "FileStreamSinkConnector",
        }
        with pytest.raises(KafkaConnectError):
            self.connect_wrapper.validate_connector_config(
                "FileStreamSinkConnector",
                kafka_connect_config=KafkaConnectConfig(**configs),
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectConfig(**configs).dict(),
        )

    @patch("requests.put")
    def test_should_create_correct_validate_connector_config_and_name_gets_added(
        self, mock_put: MagicMock
    ):
        connector_name = "FileStreamSinkConnector"
        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
        }
        with pytest.raises(KafkaConnectError):
            self.connect_wrapper.validate_connector_config(
                connector_name,
                kafka_connect_config=KafkaConnectConfig(**configs),
            )

        mock_put.assert_called_with(
            url=f"{HOST}/connector-plugins/{connector_name}/config/validate",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=KafkaConnectConfig(**{**configs, **{"name": connector_name}}).dict(),
        )

    @responses.activate
    def test_should_parse_validate_connector_config(self):
        with open(
            DEFAULTS_PATH / "connect_validation_response.json",
        ) as f:
            actual_response = json.load(f)
        responses.add(
            responses.PUT,
            f"{HOST}/connector-plugins/FileStreamSinkConnector/config/validate",
            headers=HEADERS,
            json=actual_response,
            status=200,
        )

        configs = {
            "connector.class": "org.apache.kafka.connect.file.FileStreamSinkConnector",
            "tasks.max": "1",
            "topics": "test-topic",
        }
        errors = self.connect_wrapper.validate_connector_config(
            "FileStreamSinkConnector",
            kafka_connect_config=KafkaConnectConfig(**configs),
        )

        assert errors == [
            "Found error for field file: Missing required configuration 'file' which has no default value."
        ]
