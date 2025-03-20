from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components import HelmApp
from kpops.components.streams_bootstrap.producer.producer_app import (
    ProducerApp,
    ProducerAppCleaner,
)
from kpops.components.streams_bootstrap.streams.streams_app import (
    StreamsApp,
    StreamsAppCleaner,
)

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache", "clear_kpops_config")
class TestClean:
    @pytest.fixture(autouse=True)
    def helm_mock(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.patch(
            "kpops.component_handlers.helm_wrapper.helm.Helm",
            return_value=AsyncMock(),
        )

    # TODO: test using public Pipeline API
    # @pytest.fixture()
    # def pipeline(self) -> Pipeline:
    #     pipeline = Pipeline()
    #     pipeline.add(
    #         ProducerApp(
    #             name="producer",
    #             namespace="test-namespace",
    #             values=ProducerAppValues(
    #                 streams=ProducerStreamsConfig(brokers=get_config().kafka_brokers)
    #             ),
    #         )
    #     )
    #     return pipeline

    def test_order(self, mocker: MockerFixture):
        # destroy
        producer_app_mock_destroy = mocker.patch.object(ProducerApp, "destroy")
        streams_app_mock_destroy = mocker.patch.object(StreamsApp, "destroy")
        helm_app_mock_destroy = mocker.patch.object(HelmApp, "destroy")

        # clean
        streams_app_mock_clean = mocker.patch.object(StreamsAppCleaner, "clean")
        producer_app_mock_clean = mocker.patch.object(ProducerAppCleaner, "clean")

        async_mocker = mocker.AsyncMock()
        async_mocker.attach_mock(producer_app_mock_destroy, "producer_app_mock_destroy")
        async_mocker.attach_mock(streams_app_mock_destroy, "streams_app_mock_destroy")
        async_mocker.attach_mock(helm_app_mock_destroy, "helm_app_mock_destroy")

        async_mocker.attach_mock(producer_app_mock_clean, "producer_app_mock_clean")
        async_mocker.attach_mock(streams_app_mock_clean, "streams_app_mock_clean")

        result = runner.invoke(
            app,
            [
                "clean",
                str(RESOURCE_PATH / "simple-pipeline" / "pipeline.yaml"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        # check called
        producer_app_mock_destroy.assert_called_once_with(True)
        streams_app_mock_destroy.assert_called_once_with(True)
        helm_app_mock_destroy.assert_called_once_with(True)

        producer_app_mock_clean.assert_called_once_with(True)
        streams_app_mock_clean.assert_called_once_with(True)

        # check reverse order
        assert async_mocker.mock_calls == [
            # HelmApp
            mocker.call.helm_app_mock_destroy(True),
            # StreamsApp
            mocker.call.streams_app_mock_destroy(True),
            mocker.call.streams_app_mock_clean(True),
            # ProducerApp
            mocker.call.producer_app_mock_destroy(True),
            mocker.call.producer_app_mock_clean(True),
        ]
