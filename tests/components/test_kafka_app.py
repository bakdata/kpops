from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.components.base_components import KafkaApp

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestKafkaApp:
    @pytest.fixture
    def config(self) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            helm_diff_config=HelmDiffConfig(
                enable=False,
            ),
        )

    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    def test_default_configs(self, config: PipelineConfig, handlers: ComponentHandlers):
        kafka_app = KafkaApp(
            name="example-name",
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {
                        "outputTopic": "test",
                        "brokers": "fake-broker:9092",
                    },
                },
            },
        )
        assert kafka_app.app.streams.brokers == "fake-broker:9092"

        assert kafka_app.repo_config == HelmRepoConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://bakdata.github.io/streams-bootstrap/",
        )
        assert kafka_app.version == "2.9.0"
        assert kafka_app.namespace == "test-namespace"

    def test_should_deploy_kafka_app(
        self, config: PipelineConfig, handlers: ComponentHandlers, mocker: MockerFixture
    ):
        kafka_app = KafkaApp(
            name="example-name",
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {
                    "streams": {
                        "outputTopic": "test",
                        "brokers": "fake-broker:9092",
                    },
                },
                "version": "1.2.3",
            },
        )
        helm_upgrade_install = mocker.patch.object(kafka_app.helm, "upgrade_install")
        mocker.patch.object(kafka_app, "get_helm_chart", return_value="test/test-chart")

        kafka_app.deploy(True)

        helm_upgrade_install.assert_called_once_with(
            "example-name",
            "test/test-chart",
            True,
            "test-namespace",
            {
                "streams": {"brokers": "fake-broker:9092", "outputTopic": "test"},
            },
            HelmUpgradeInstallFlags(version="1.2.3"),
        )
