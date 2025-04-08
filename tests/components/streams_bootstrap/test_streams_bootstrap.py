import re
from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest
from _pytest.python_api import RaisesContext
from pydantic import ValidationError
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.common.kubernetes_model import (
    NodeAffinity,
    NodeSelectorTerm,
    PreferredSchedulingTerm,
    ResourceDefinition,
)
from kpops.components.streams_bootstrap.base import StreamsBootstrap
from kpops.components.streams_bootstrap.model import StreamsBootstrapValues


@pytest.mark.usefixtures("mock_env")
class TestStreamsBootstrap:
    def test_default_configs(self):
        streams_bootstrap = StreamsBootstrap.model_validate(
            {
                "name": "example-name",
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
        assert streams_bootstrap.version == "3.6.1"
        assert streams_bootstrap.namespace == "test-namespace"
        assert streams_bootstrap.values.image_tag is None

    async def test_should_deploy_streams_bootstrap_app(self, mocker: MockerFixture):
        streams_bootstrap = StreamsBootstrap.model_validate(
            {
                "name": "example-name",
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
            streams_bootstrap._helm, "upgrade_install"
        )
        print_helm_diff = mocker.patch.object(
            streams_bootstrap._dry_run_handler, "print_helm_diff"
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
                "fullnameOverride": "${pipeline.name}-example-name",
                "image": "streamsBootstrap",
                "imageTag": "1.0.0",
                "kafka": {
                    "bootstrapServers": "fake-broker:9092",
                    "outputTopic": "test",
                },
            },
            HelmUpgradeInstallFlags(version="3.2.1"),
        )

    async def test_should_raise_validation_error_for_invalid_image_tag(self):
        with pytest.raises(
            ValidationError,
            match=re.escape(
                "1 validation error for StreamsBootstrapValues\nimageTag\n  String should match pattern '^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$'"
            ),
        ):
            assert StreamsBootstrapValues.model_validate(
                {
                    "image": "streamsBootstrap",
                    "imageTag": "invalid image tag!",
                    "kafka": {
                        "bootstrapServers": "fake-broker:9092",
                    },
                }
            )

    async def test_should_not_raise_validation_error_for_helm_chart_version_4(self):
        assert StreamsBootstrap.model_validate(
            {
                "name": "example-name",
                "namespace": "test-namespace",
                "values": {
                    "image": "my-app",
                    "imageTag": "1.0.0",
                    "kafka": {
                        "outputTopic": "test",
                        "bootstrapServers": "fake-broker:9092",
                    },
                },
                "version": "4.0.0",
            },
        )

    async def test_should_raise_validation_error_for_invalid_helm_chart_version(self):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "When using the streams-bootstrap component your version ('2.1.0') must be at least 3.0.1."
            ),
        ):
            assert StreamsBootstrap.model_validate(
                {
                    "name": "example-name",
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

    def test_should_raise_validation_error_for_unsupported_attribute(self):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "streams-bootstrap v3 no longer supports 'streams' attribute."
            ),
        ):
            assert StreamsBootstrap.model_validate(
                {
                    "name": "example-name",
                    "namespace": "test-namespace",
                    "values": {
                        "image": "streamsBootstrap",
                        "kafka": {
                            "bootstrapServers": "localhost:9092",
                        },
                        "streams": {},
                    },
                },
            )

    @pytest.mark.parametrize(
        ("input", "expectation"),
        [
            pytest.param({"cpu": 1}, does_not_raise(), id="cpu int"),
            pytest.param({"cpu": "1"}, does_not_raise(), id="cpu str without unit"),
            pytest.param({"cpu": "10m"}, does_not_raise(), id="cpu str milli CPU"),
            pytest.param(
                {"cpu": "100foo"},
                pytest.raises(ValidationError),
                id="cpu str disallow regex mismatch",
            ),
            pytest.param(
                {"cpu": 0}, pytest.raises(ValidationError), id="cpu int disallow 0"
            ),
            pytest.param(
                {"cpu": -1},
                pytest.raises(ValidationError),
                id="cpu int disallow negative",
            ),
            pytest.param({"memory": 1}, does_not_raise(), id="memory int"),
            pytest.param(
                {"memory": "1"}, does_not_raise(), id="memory str without unit"
            ),
            pytest.param({"memory": "10G"}, does_not_raise(), id="memory str gigabyte"),
            pytest.param({"memory": "1Gi"}, does_not_raise(), id="memory str gibibyte"),
            pytest.param({"memory": "10M"}, does_not_raise(), id="memory str megabyte"),
            pytest.param(
                {"memory": "10Mi"}, does_not_raise(), id="memory str mebibyte"
            ),
            pytest.param(
                {"memory": "2.5G"}, does_not_raise(), id="memory str decimal gigabyte"
            ),
            pytest.param(
                {"memory": "0.599M"},
                does_not_raise(),
                id="memory str decimal megabyte",
            ),
            pytest.param(
                {"memory": 0},
                pytest.raises(ValidationError),
                id="memory int disallow 0",
            ),
            pytest.param(
                {"memory": -1},
                pytest.raises(ValidationError),
                id="memory int disallow negative",
            ),
            pytest.param(
                {"ephemeral-storage": "10G"},
                does_not_raise(),
                id="ephemeral-storage str gigabyte",
            ),
            pytest.param(
                {"ephemeral-storage": "1Gi"},
                does_not_raise(),
                id="ephemeral-storage str gibibyte",
            ),
            pytest.param(
                {"ephemeral-storage": "10M"},
                does_not_raise(),
                id="ephemeral-storage str megabyte",
            ),
            pytest.param(
                {"ephemeral-storage": "10Mi"},
                does_not_raise(),
                id="ephemeral-storage str mebibyte",
            ),
            pytest.param(
                {"ephemeral-storage": "2.5G"},
                does_not_raise(),
                id="ephemeral-storage str decimal gigabyte",
            ),
            pytest.param(
                {"ephemeral-storage": "0.599M"},
                does_not_raise(),
                id="ephemeral-storage str decimal megabyte",
            ),
            pytest.param(
                {"ephemeral-storage": 0},
                pytest.raises(ValidationError),
                id="ephemeral-storage int disallow 0",
            ),
            pytest.param(
                {"ephemeral-storage": -1},
                pytest.raises(ValidationError),
                id="ephemeral-storage int disallow negative",
            ),
        ],
    )
    def test_resource_definition(
        self,
        input: dict[str, Any],
        expectation: RaisesContext[ValidationError] | does_not_raise[None],
    ):
        with expectation:
            assert ResourceDefinition.model_validate(input)

    def test_node_affinity(self):
        node_affinity = NodeAffinity()
        assert node_affinity.preferred_during_scheduling_ignored_during_execution == []
        assert node_affinity.model_dump(by_alias=True) == {
            "requiredDuringSchedulingIgnoredDuringExecution": None,
            "preferredDuringSchedulingIgnoredDuringExecution": None,
        }
        assert node_affinity.model_dump(by_alias=True, exclude_none=True) == {}

        node_affinity.preferred_during_scheduling_ignored_during_execution.append(
            PreferredSchedulingTerm(preference=NodeSelectorTerm(), weight=1)
        )
        assert node_affinity.model_dump(by_alias=True, exclude_none=True) == {
            "preferredDuringSchedulingIgnoredDuringExecution": [
                {
                    "preference": {},
                    "weight": 1,
                }
            ],
        }
