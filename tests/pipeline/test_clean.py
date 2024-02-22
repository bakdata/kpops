from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache")
class TestClean:
    @pytest.fixture(autouse=True)
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        async_mock = AsyncMock()
        return mocker.patch(
            "kpops.components.base_components.helm_app.Helm",
            return_value=async_mock,
        ).return_value

    # TODO: test using public Pipeline API
    # @pytest.fixture()
    # def config(self) -> KpopsConfig:
    #     return KpopsConfig()

    # @pytest.fixture()
    # def handlers(self) -> ComponentHandlers:
    #     return ComponentHandlers(
    #         schema_handler=AsyncMock(),
    #         connector_handler=AsyncMock(),
    #         topic_handler=AsyncMock(),
    #     )

    # @pytest.fixture()
    # def pipeline(self, config: KpopsConfig, handlers: ComponentHandlers) -> Pipeline:
    #     kwargs = {"config": config, "handlers": handlers}
    #     pipeline = Pipeline()
    #     pipeline.add(
    #         ProducerApp(
    #             name="producer",
    #             namespace="test-namespace",
    #             app=ProducerAppValues(
    #                 streams=ProducerStreamsConfig(brokers=config.kafka_brokers)
    #             ),
    #             **kwargs,
    #         )
    #     )
    #     return pipeline

    def test_order(self, mocker: MockerFixture):
        producer_app_mock_clean = mocker.patch(
            "kpops.components.streams_bootstrap.producer.producer_app.ProducerApp.clean",
        )
        streams_app_mock_clean = mocker.patch(
            "kpops.components.streams_bootstrap.streams.streams_app.StreamsApp.clean",
        )
        helm_app_mock_clean = mocker.patch(
            "kpops.components.base_components.helm_app.HelmApp.clean",
        )
        mock_clean = mocker.AsyncMock()
        mock_clean.attach_mock(producer_app_mock_clean, "producer_app_mock_clean")
        mock_clean.attach_mock(streams_app_mock_clean, "streams_app_mock_clean")
        mock_clean.attach_mock(helm_app_mock_clean, "helm_app_mock_clean")

        result = runner.invoke(
            app,
            [
                "clean",
                str(RESOURCE_PATH / "simple-pipeline" / "pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        # check called
        producer_app_mock_clean.assert_called_once_with(True)
        streams_app_mock_clean.assert_called_once_with(True)
        helm_app_mock_clean.assert_called_once_with(True)

        # check reverse order
        assert mock_clean.mock_calls == [
            mocker.call.helm_app_mock_clean(True),
            mocker.call.streams_app_mock_clean(True),
            mocker.call.producer_app_mock_clean(True),
        ]
