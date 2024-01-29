from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.streams_bootstrap import StreamsBootstrap
from kpops.config import KpopsConfig
from kpops.utils.environment import ENV

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestStreamsBootstrap:
    @pytest.fixture()
    def config(self) -> KpopsConfig:
        ENV["pipeline_path"] = str(DEFAULTS_PATH / "pipelines/pipeline-1/pipeline.yaml")
        return KpopsConfig(
            # pipeline_path=DEFAULTS_PATH / "pipelines/pipeline-1/pipeline.yaml",
            helm_diff_config=HelmDiffConfig(),
        )

    @pytest.fixture()
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    def test_default_configs(self, config: KpopsConfig, handlers: ComponentHandlers):
        streams_bootstrap = StreamsBootstrap(
            name="example-name",
            config=config,
            handlers=handlers,
            **{
                "namespace": "test-namespace",
                "app": {},
            },
        )
        assert streams_bootstrap.repo_config == HelmRepoConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://bakdata.github.io/streams-bootstrap/",
        )
        assert streams_bootstrap.version == "2.9.0"
        assert streams_bootstrap.namespace == "test-namespace"

    def test_should_deploy_streams_bootstrap_app(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
    ):
        streams_bootstrap = StreamsBootstrap(
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
        helm_upgrade_install = mocker.patch.object(
            streams_bootstrap.helm, "upgrade_install"
        )
        print_helm_diff = mocker.patch.object(
            streams_bootstrap.dry_run_handler, "print_helm_diff"
        )
        mocker.patch.object(
            StreamsBootstrap,
            "helm_chart",
            return_value="test/test-chart",
            new_callable=mocker.PropertyMock,
        )

        streams_bootstrap.deploy(dry_run=True)

        print_helm_diff.assert_called_once()
        helm_upgrade_install.assert_called_once_with(
            create_helm_release_name("${pipeline.name}-example-name"),
            "test/test-chart",
            True,
            "test-namespace",
            {
                "nameOverride": "${pipeline.name}-example-name",
                "streams": {
                    "brokers": "fake-broker:9092",
                    "outputTopic": "test",
                },
            },
            HelmUpgradeInstallFlags(version="1.2.3"),
        )
