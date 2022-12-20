from unittest import mock
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.pipeline_deployer.kafka_connect.connect_wrapper import ConnectWrapper
from kpops.pipeline_deployer.kafka_connect.exception import ConnectorNotFoundException
from kpops.pipeline_deployer.kafka_connect.handler import ConnectorHandler
from kpops.pipeline_deployer.kafka_connect.model import (
    KafkaConnectConfig,
    KafkaConnectorType,
)
from kpops.pipeline_deployer.streams_bootstrap.helm_wrapper import HelmCommandConfig
from kpops.utils.colorify import greenify, magentaify, yellowify

CONNECTOR_NAME = "test-connector"


class TestConnectorHandler:
    @pytest.fixture(autouse=True)
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.pipeline_deployer.kafka_connect.handler.log.info")

    @pytest.fixture(autouse=True)
    def log_warning_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.pipeline_deployer.kafka_connect.handler.log.warning")

    @pytest.fixture(autouse=True)
    def log_error_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.pipeline_deployer.kafka_connect.handler.log.error")

    @pytest.fixture(autouse=True)
    def renderer_diff_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.pipeline_deployer.kafka_connect.handler.render_diff")

    def test_should_create_connector_in_dry_run(
        self, renderer_diff_mock: MagicMock, log_info_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()
        renderer_diff_mock.return_value = None

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        config = KafkaConnectConfig()
        handler.create_connector(CONNECTOR_NAME, config, True)
        connector_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connector_wrapper.validate_connector_config.assert_called_once_with(config)

        log_info_mock.assert_has_calls(
            [
                mock.call.log_info(
                    yellowify(
                        f"Connector Creation: connector {CONNECTOR_NAME} already exists."
                    )
                ),
                mock.call.log_info(
                    greenify(
                        f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
                    )
                ),
            ]
        )

    def test_should_log_correct_message_when_create_connector_and_connector_not_exists_in_dry_run(
        self, log_info_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()

        config = KafkaConnectConfig()
        handler.create_connector(CONNECTOR_NAME, config, True)
        connector_wrapper.get_connector.assert_called_once_with(CONNECTOR_NAME)
        connector_wrapper.validate_connector_config.assert_called_once_with(config)

        log_info_mock.assert_has_calls(
            [
                mock.call.log_info(
                    greenify(
                        f"Connector Creation: connector {CONNECTOR_NAME} does not exist. Creating connector with config:\n {config}"
                    )
                ),
                mock.call.log_info(
                    greenify(
                        f"Connector Creation: connector config for {CONNECTOR_NAME} is valid!"
                    )
                ),
            ]
        )

    def test_should_log_invalid_config_when_create_connector_in_dry_run(
        self, renderer_diff_mock: MagicMock, log_error_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()

        errors = [
            "Missing required configuration file which has no default value.",
            "Missing connector name.",
        ]
        connector_wrapper.validate_connector_config.return_value = errors

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        config = KafkaConnectConfig()

        with pytest.raises(SystemExit):
            handler.create_connector(CONNECTOR_NAME, config, True)

        connector_wrapper.validate_connector_config.assert_called_once_with(config)

        log_error_mock.assert_has_calls(
            [
                mock.call.log_error(
                    f"Connector Creation: validating the connector config for connector {CONNECTOR_NAME} resulted in the following errors:"
                ),
                mock.call.log_error("\n".join(errors)),
            ]
        )

    def test_should_call_update_connector_config_when_connector_exists_not_dry_run(
        self,
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        config = KafkaConnectConfig()
        handler.create_connector(CONNECTOR_NAME, config, False)

        connector_wrapper.assert_has_calls(
            [
                mock.call.get_connector(CONNECTOR_NAME),
                mock.call.update_connector_config(CONNECTOR_NAME, config),
            ]
        )

    def test_should_call_create_connector_when_connector_does_not_exists_not_dry_run(
        self,
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        config = KafkaConnectConfig()
        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()
        handler.create_connector(CONNECTOR_NAME, config, False)

        connector_wrapper.create_connector.assert_called_once_with(
            CONNECTOR_NAME, config
        )

    def test_should_print_correct_log_when_destroying_connector_in_dry_run(
        self, log_info_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        handler.destroy_connector(CONNECTOR_NAME, True)

        log_info_mock.assert_called_once_with(
            magentaify(
                f"Connector Destruction: connector {CONNECTOR_NAME} already exists. Deleting connector."
            )
        )

    def test_should_print_correct_warning_log_when_destroying_connector_and_connector_exists_in_dry_run(
        self, log_warning_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()
        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        handler.destroy_connector(CONNECTOR_NAME, True)

        log_warning_mock.assert_called_once_with(
            f"Connector Destruction: connector {CONNECTOR_NAME} does not exist and cannot be deleted. Skipping."
        )

    def test_should_call_delete_connector_when_destroying_existing_connector_not_dry_run(
        self,
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        handler.destroy_connector(CONNECTOR_NAME, False)
        connector_wrapper.assert_has_calls(
            [
                mock.call.get_connector(CONNECTOR_NAME),
                mock.call.delete_connector(CONNECTOR_NAME),
            ]
        )

    def test_should_print_correct_warning_log_when_destroying_connector_and_connector_exists_not_dry_run(
        self, log_warning_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        connector_wrapper = MagicMock()
        connector_wrapper.get_connector.side_effect = ConnectorNotFoundException()

        handler = ConnectorHandler(
            connector_wrapper, 0, helm_wrapper, "test-namespace", "broker:9092", {}
        )
        handler.destroy_connector(CONNECTOR_NAME, False)

        log_warning_mock.assert_called_once_with(
            f"Connector Destruction: the connector {CONNECTOR_NAME} does not exist. Skipping."
        )

    def test_should_call_helm_upgrade_install_and_uninstall_when_clean_connector_with_retain_clean_jobs_true(
        self, log_info_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        values = {
            "config": {
                "brokers": "127.0.0.1",
                "connector": CONNECTOR_NAME,
                "offsetTopic": "kafka-connect-offsets",
            },
            "connectorType": "source",
            "nameOverride": CONNECTOR_NAME,
        }
        handler = ConnectorHandler(
            ConnectWrapper("test"),
            0,
            helm_wrapper,
            "test-namespace",
            "broker:9092",
            values,
        )
        handler.clean_connector(
            connector_name=CONNECTOR_NAME,
            connector_type=KafkaConnectorType.SOURCE,
            dry_run=True,
            retain_clean_jobs=True,
            offset_topic="kafka-connect-offsets",
        )

        log_info_mock.assert_has_calls(
            [
                mock.call.log_info(
                    magentaify(
                        f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {CONNECTOR_NAME}"
                    )
                ),
                mock.call.log_info(
                    magentaify(
                        f"Connector Cleanup: deploy Connect {KafkaConnectorType.SOURCE.value} resetter for {CONNECTOR_NAME}"
                    )
                ),
            ]
        )

        helm_wrapper.assert_has_calls(
            [
                mock.call.helm_uninstall(
                    namespace="test-namespace",
                    release_name="test-connector-clean",
                    suffix="-clean",
                    dry_run=True,
                ),
                mock.call.helm_upgrade_install(
                    app="kafka-connect-resetter",
                    dry_run=True,
                    helm_command_config=HelmCommandConfig(
                        debug=False,
                        force=False,
                        timeout="5m0s",
                        wait=True,
                        wait_for_jobs=True,
                    ),
                    namespace="test-namespace",
                    release_name="test-connector-clean",
                    suffix="-clean",
                    values=values,
                ),
            ]
        )

    def test_should_call_helm_upgrade_install_and_uninstall_when_clean_connector_with_retain_clean_jobs_false(
        self, log_info_mock: MagicMock
    ):
        helm_wrapper = MagicMock()
        values = {
            "config": {
                "brokers": "127.0.0.1",
                "connector": CONNECTOR_NAME,
                "offsetTopic": "kafka-connect-offsets",
            },
            "connectorType": "source",
            "nameOverride": CONNECTOR_NAME,
        }
        handler = ConnectorHandler(
            ConnectWrapper("test"),
            0,
            helm_wrapper,
            "test-namespace",
            "broker:9092",
            values,
        )
        handler.clean_connector(
            connector_name=CONNECTOR_NAME,
            connector_type=KafkaConnectorType.SOURCE,
            dry_run=True,
            retain_clean_jobs=False,
            offset_topic="kafka-connect-offsets",
        )

        log_info_mock.assert_has_calls(
            [
                mock.call.log_info(
                    magentaify(
                        f"Connector Cleanup: uninstalling cleanup job Helm release from previous runs for {CONNECTOR_NAME}"
                    )
                ),
                mock.call.log_info(
                    magentaify(
                        f"Connector Cleanup: deploy Connect {KafkaConnectorType.SOURCE.value} resetter for {CONNECTOR_NAME}"
                    )
                ),
                mock.call.log_info(
                    magentaify("Connector Cleanup: uninstall cleanup job")
                ),
            ]
        )

        helm_wrapper.assert_has_calls(
            [
                mock.call.helm_uninstall(
                    namespace="test-namespace",
                    release_name="test-connector-clean",
                    suffix="-clean",
                    dry_run=True,
                ),
                mock.call.helm_upgrade_install(
                    app="kafka-connect-resetter",
                    dry_run=True,
                    helm_command_config=HelmCommandConfig(
                        debug=False,
                        force=False,
                        timeout="5m0s",
                        wait=True,
                        wait_for_jobs=True,
                    ),
                    namespace="test-namespace",
                    release_name="test-connector-clean",
                    suffix="-clean",
                    values=values,
                ),
                mock.call.helm_uninstall(
                    namespace="test-namespace",
                    release_name="test-connector-clean",
                    suffix="-clean",
                    dry_run=True,
                ),
            ]
        )
