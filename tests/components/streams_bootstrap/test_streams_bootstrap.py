import re

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.common.kubernetes_model import ResourceDefinition
from kpops.components.streams_bootstrap.base import StreamsBootstrap
from kpops.components.streams_bootstrap.model import StreamsBootstrapValues


@pytest.mark.usefixtures("mock_env")
class TestStreamsBootstrap:
    def test_default_configs(self):
        streams_bootstrap = StreamsBootstrap(
            name="example-name",
            **{
                "namespace": "test-namespace",
                "values": {
                    "image": "streamsBootstrap",
                    "kafka": {
                        "bootstrapServers": "localhost:9092",
                    },
                },
            },
        )
        assert streams_bootstrap.repo_config == HelmRepoConfig(
            repository_name="bakdata-streams-bootstrap",
            url="https://bakdata.github.io/streams-bootstrap/",
        )
        assert streams_bootstrap.version == "3.0.1"
        assert streams_bootstrap.namespace == "test-namespace"
        assert streams_bootstrap.values.image_tag is None

    @pytest.mark.asyncio()
    async def test_should_deploy_streams_bootstrap_app(self, mocker: MockerFixture):
        streams_bootstrap = StreamsBootstrap(
            name="example-name",
            **{
                "namespace": "test-namespace",
                "values": {
                    "image": "streamsBootstrap",
                    "imageTag": "1.0.0",
                    "kafka": {
                        "outputTopic": "test",
                        "bootstrapServers": "fake-broker:9092",
                    },
                },
                "version": "3.2.1",
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

        await streams_bootstrap.deploy(dry_run=True)

        print_helm_diff.assert_called_once()
        helm_upgrade_install.assert_called_once_with(
            create_helm_release_name("${pipeline.name}-example-name"),
            "test/test-chart",
            True,
            "test-namespace",
            {
                "nameOverride": "${pipeline.name}-example-name",
                "image": "streamsBootstrap",
                "imageTag": "1.0.0",
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "outputTopic": "test",
                },
            },
            HelmUpgradeInstallFlags(version="3.2.1"),
        )

    @pytest.mark.asyncio()
    async def test_should_raise_validation_error_for_invalid_image_tag(self):
        with pytest.raises(
            ValidationError,
            match=re.escape(
                "1 validation error for StreamsBootstrapValues\nimageTag\n  String should match pattern '^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$'"
            ),
        ):
            StreamsBootstrapValues(
                **{
                    "image": "streamsBootstrap",
                    "imageTag": "invalid image tag!",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                    },
                }
            )

    @pytest.mark.asyncio()
    async def test_should_raise_validation_error_for_invalid_helm_chart_version(self):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "When using the streams-bootstrap component your version ('2.1.0') must be at least 3.0.1."
            ),
        ):
            StreamsBootstrap(
                name="example-name",
                **{
                    "namespace": "test-namespace",
                    "values": {
                        "imageTag": "1.0.0",
                        "kafka": {
                            "outputTopic": "test",
                            "bootstrapServers": "fake-broker:9092",
                        },
                    },
                    "version": "2.1.0",
                },
            )

    def test_resource_definition(self):
        assert ResourceDefinition(cpu=1)
        assert ResourceDefinition(cpu="1")
        assert ResourceDefinition(cpu="1m")
        assert ResourceDefinition(cpu="100m")
        with pytest.raises(ValidationError):
            ResourceDefinition(cpu="100foo")
        with pytest.raises(ValidationError):
            ResourceDefinition(cpu=-1)
