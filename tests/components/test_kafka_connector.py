import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig
from kpops.component_handlers.kafka_connect.model import KafkaConnectorConfig
from kpops.components.base_components.kafka_connector import KafkaConnector
from kpops.config import KpopsConfig, TopicNameConfig

DEFAULTS_PATH = Path(__file__).parent / "resources"
CONNECTOR_NAME = "test-connector-with-long-name-0123456789abcdefghijklmnop"
CONNECTOR_FULL_NAME = "${pipeline_name}-" + CONNECTOR_NAME
CONNECTOR_CLEAN_FULL_NAME = CONNECTOR_FULL_NAME + "-clean"
CONNECTOR_CLEAN_RELEASE_NAME = "${pipeline_name}-test-connector-with-lon-449ec-clean"
CONNECTOR_CLASS = "com.bakdata.connect.TestConnector"


class TestKafkaConnector:
    @pytest.fixture()
    def config(self) -> KpopsConfig:
        return KpopsConfig(
            defaults_path=DEFAULTS_PATH,
            topic_name_config=TopicNameConfig(
                default_error_topic_name="${component_type}-error-topic",
                default_output_topic_name="${component_type}-output-topic",
            ),
            kafka_brokers="broker:9092",
            helm_diff_config=HelmDiffConfig(),
        )

    @pytest.fixture()
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    @pytest.fixture(autouse=True)
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.kafka_connector.Helm"
        ).return_value

    @pytest.fixture()
    def dry_run_handler(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.kafka_connector.DryRunHandler"
        ).return_value

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig(
            **{
                "connector.class": CONNECTOR_CLASS,
                "name": CONNECTOR_FULL_NAME,
            }
        )

    def test_connector_config_name_override(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            namespace="test-namespace",
        )
        assert connector.app.name == CONNECTOR_FULL_NAME

        connector = KafkaConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app={"connector.class": CONNECTOR_CLASS},  # type: ignore[reportGeneralTypeIssues]
            namespace="test-namespace",
        )
        assert connector.app.name == CONNECTOR_FULL_NAME

        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Connector name 'different-name' should be the same as component name '{CONNECTOR_FULL_NAME}'"
            ),
        ):
            KafkaConnector(
                name=CONNECTOR_NAME,
                config=config,
                handlers=handlers,
                app={"connector.class": CONNECTOR_CLASS, "name": "different-name"},  # type: ignore[reportGeneralTypeIssues]
                namespace="test-namespace",
            )

        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Connector name '' should be the same as component name '{CONNECTOR_FULL_NAME}'"
            ),
        ):
            KafkaConnector(
                name=CONNECTOR_NAME,
                config=config,
                handlers=handlers,
                app={"connector.class": CONNECTOR_CLASS, "name": ""},  # type: ignore[reportGeneralTypeIssues]
                namespace="test-namespace",
            )

    def test_resetter_release_name(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        connector_config: KafkaConnectorConfig,
    ):
        connector = KafkaConnector(
            name=CONNECTOR_NAME,
            config=config,
            handlers=handlers,
            app=connector_config,
            namespace="test-namespace",
        )
        assert connector.app.name == CONNECTOR_FULL_NAME
        assert connector._resetter_release_name == CONNECTOR_CLEAN_RELEASE_NAME
