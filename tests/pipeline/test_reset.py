from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from kpops.cli.main import app
from kpops.components.base_components import HelmApp
from kpops.components.streams_bootstrap import ProducerApp, StreamsApp
from kpops.components.streams_bootstrap.producer.producer_app import (
    ProducerAppCleaner,
)
from kpops.components.streams_bootstrap.streams.streams_app import StreamsAppCleaner

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


@pytest.mark.usefixtures("mock_env", "load_yaml_file_clear_cache", "clear_kpops_config")
class TestReset:
    @pytest.fixture(autouse=True)
    def helm_mock(self, mocker: MockerFixture) -> AsyncMock:
        return mocker.patch(
            "kpops.component_handlers.helm_wrapper.helm.Helm",
            return_value=AsyncMock(),
        )

    def test_order(self, mocker: MockerFixture):
        # destroy
        producer_app_mock_destroy = mocker.patch.object(ProducerApp, "destroy")
        streams_app_mock_destroy = mocker.patch.object(StreamsApp, "destroy")
        helm_app_mock_destroy = mocker.patch.object(HelmApp, "destroy")

        # reset
        streams_app_mock_reset = mocker.patch.object(StreamsAppCleaner, "reset")
        producer_app_mock_reset = mocker.patch.object(ProducerAppCleaner, "reset")

        async_mocker = mocker.AsyncMock()
        async_mocker.attach_mock(producer_app_mock_destroy, "producer_app_mock_destroy")
        async_mocker.attach_mock(streams_app_mock_destroy, "streams_app_mock_destroy")
        async_mocker.attach_mock(helm_app_mock_destroy, "helm_app_mock_destroy")

        async_mocker.attach_mock(producer_app_mock_reset, "producer_app_mock_reset")
        async_mocker.attach_mock(streams_app_mock_reset, "streams_app_mock_reset")

        result = runner.invoke(
            app,
            [
                "reset",
                str(RESOURCE_PATH / "simple-pipeline" / "pipeline.yaml"),
            ],
            catch_exceptions=False,
        )

        assert result.exit_code == 0, result.stdout

        # check called
        producer_app_mock_destroy.assert_called_once_with(True)
        streams_app_mock_destroy.assert_called_once_with(True)
        helm_app_mock_destroy.assert_called_once_with(True)

        producer_app_mock_reset.assert_not_called()
        streams_app_mock_reset.assert_called_once_with(True)

        # check reverse order
        assert async_mocker.mock_calls == [
            # HelmApp
            mocker.call.helm_app_mock_destroy(True),
            # StreamsApp
            mocker.call.streams_app_mock_destroy(True),
            mocker.call.streams_app_mock_reset(True),
            # ProducerApp
            mocker.call.producer_app_mock_destroy(True),
        ]
