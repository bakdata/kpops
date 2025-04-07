import re

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.streams_bootstrap_v2 import StreamsBootstrapV2
from kpops.components.streams_bootstrap_v2.base import StreamsBootstrapV2Values


@pytest.mark.filterwarnings("ignore:.*StreamsBootstrapV2.*:DeprecationWarning")
@pytest.mark.usefixtures("mock_env")
class TestStreamsBootstrap:
    def test_default_configs(self):
        streams_bootstrap = StreamsBootstrapV2.model_validate(
            {
                "name": "example-name",
                "namespace": "test-namespace",
                "values": {
                    "streams": {
                        "brokers": "localhost:9092",
                    }
                },
            },
        )
        assert streams_bootstrap.repo_config == HelmRepoConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://bakdata.github.io/streams-bootstrap/",
        )
        assert streams_bootstrap.version == "2.9.0"
        assert streams_bootstrap.namespace == "test-namespace"
        assert streams_bootstrap.values.image_tag == "latest"

    async def test_should_deploy_streams_bootstrap_app(self, mocker: MockerFixture):
        streams_bootstrap = StreamsBootstrapV2.model_validate(
            {
                "name": "example-name",
                "namespace": "test-namespace",
                "values": {
                    "imageTag": "1.0.0",
                    "streams": {
                        "outputTopic": "test",
                        "brokers": "fake-broker:9092",
                    },
                },
                "version": "1.2.3",
            },
        )
        helm_upgrade_install = mocker.patch.object(
            streams_bootstrap._helm, "upgrade_install"
        )
        print_helm_diff = mocker.patch.object(
            streams_bootstrap._dry_run_handler, "print_helm_diff"
        )
        mocker.patch.object(
            StreamsBootstrapV2,
            "helm_chart",
            return_value="test/test-chart",
            new_callable=mocker.PropertyMock,
        )

        await streams_bootstrap.deploy(dry_run=True)

        print_helm_diff.assert_called_once()
        helm_upgrade_install.assert_called_once_with(
            create_helm_release_name("${pipeline.name}-example-name"),
            "test/test-chart",
            True,
            "test-namespace",
            {
                "nameOverride": "${pipeline.name}-example-name",
                "fullnameOverride": "${pipeline.name}-example-name",
                "imageTag": "1.0.0",
                "streams": {
                    "brokers": "fake-broker:9092",
                    "outputTopic": "test",
                },
            },
            HelmUpgradeInstallFlags(version="1.2.3"),
        )

    async def test_should_raise_validation_error_for_invalid_image_tag(self):
        with pytest.raises(
            ValidationError,
            match=re.escape(
                "1 validation error for StreamsBootstrapV2Values\nimageTag\n  String should match pattern '^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$'"
            ),
        ):
            StreamsBootstrapV2Values.model_validate(
                {
                    "imageTag": "invalid image tag!",
                    "streams": {
                        "brokers": "localhost:9092",
                    },
                }
            )
