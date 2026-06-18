import re
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.kafka_connect.model import KafkaConnectorConfig
from kpops.components.base_components.kafka_connector import (
    KafkaConnector,
)

CONNECTOR_NAME = "test-connector-with-long-name-0123456789abcdefghijklmnop"
CONNECTOR_FULL_NAME = "${pipeline.name}-" + CONNECTOR_NAME
CONNECTOR_CLEAN_FULL_NAME = CONNECTOR_FULL_NAME + "-clean"
CONNECTOR_CLEAN_HELM_NAMEOVERRIDE = (
    "${pipeline.name}-" + "test-connector-with-long-name-0123-612f3-clean"
)
CONNECTOR_CLEAN_RELEASE_NAME = (
    "${pipeline.name}-" + "test-connector-with-long-612f3-clean"
)
CONNECTOR_CLASS = "com.bakdata.connect.TestConnector"
RESETTER_NAMESPACE = "test-namespace"


@pytest.mark.usefixtures("mock_env")
class TestKafkaConnector:
    @pytest.fixture(autouse=True)
    def helm_mock(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.Helm",
            return_value=AsyncMock(),
        ).return_value

    @pytest.fixture()
    def dry_run_handler_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.helm_app.DryRunHandler"
        ).return_value

    @pytest.fixture()
    def connector_config(self) -> KafkaConnectorConfig:
        return KafkaConnectorConfig(
            connector_class=CONNECTOR_CLASS,
            name=CONNECTOR_FULL_NAME,
        )

    @pytest.fixture()
    def connector(self, connector_config: KafkaConnectorConfig) -> KafkaConnector:
        return KafkaConnector(  # HACK: not supposed to be instantiated, because ABC
            name=CONNECTOR_NAME,
            config=connector_config,
            resetter_namespace=RESETTER_NAMESPACE,
        )

    def test_connector_config_name_override(self, connector: KafkaConnector):
        assert connector.config.name == CONNECTOR_FULL_NAME

        connector = KafkaConnector(
            name=CONNECTOR_NAME,
            config={"connector.class": CONNECTOR_CLASS},  # pyright: ignore[reportArgumentType], gets enriched
            resetter_namespace=RESETTER_NAMESPACE,
        )
        assert connector.config.name == CONNECTOR_FULL_NAME

        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Connector name 'different-name' should be the same as component name '{CONNECTOR_FULL_NAME}'"
            ),
        ):
            KafkaConnector(
                name=CONNECTOR_NAME,
                config={"connector.class": CONNECTOR_CLASS, "name": "different-name"},  # pyright: ignore[reportArgumentType], gets enriched
            )

        with pytest.raises(
            ValueError,
            match=re.escape(
                f"Connector name '' should be the same as component name '{CONNECTOR_FULL_NAME}'"
            ),
        ):
            KafkaConnector(
                name=CONNECTOR_NAME,
                config={"connector.class": CONNECTOR_CLASS, "name": ""},  # pyright: ignore[reportArgumentType], gets enriched
            )
