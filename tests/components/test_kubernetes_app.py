from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmRepoConfig,
)
from kpops.component_handlers.helm_wrapper.utils import create_helm_release_name
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppValues,
)
from kpops.config import KpopsConfig

HELM_RELEASE_NAME = create_helm_release_name("${pipeline.name}-test-kubernetes-app")


class KubernetesTestValues(KubernetesAppValues):
    foo: str


class TestKubernetesApp:
    @pytest.fixture()
    def config(self) -> KpopsConfig:
        return KpopsConfig()

    @pytest.fixture()
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=AsyncMock(),
            connector_handler=AsyncMock(),
            topic_handler=AsyncMock(),
        )

    @pytest.fixture()
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.components.base_components.kubernetes_app.log.info")

    @pytest.fixture()
    def app_values(self) -> KubernetesTestValues:
        return KubernetesTestValues(foo="foo")

    @pytest.fixture()
    def repo_config(self) -> HelmRepoConfig:
        return HelmRepoConfig(repository_name="test", url="https://bakdata.com")

    @pytest.fixture()
    def kubernetes_app(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        app_values: KubernetesTestValues,
    ) -> KubernetesApp:
        return KubernetesApp(
            name="test-kubernetes-app",
            config=config,
            handlers=handlers,
            app=app_values,
            namespace="test-namespace",
        )

    def test_should_raise_value_error_when_name_is_not_valid(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        app_values: KubernetesTestValues,
    ):
        with pytest.raises(
            ValueError, match=r"The component name .* is invalid for Kubernetes."
        ):
            KubernetesApp(
                name="Not-Compatible*",
                config=config,
                handlers=handlers,
                app=app_values,
                namespace="test-namespace",
            )

        with pytest.raises(
            ValueError, match=r"The component name .* is invalid for Kubernetes."
        ):
            KubernetesApp(
                name="snake_case*",
                config=config,
                handlers=handlers,
                app=app_values,
                namespace="test-namespace",
            )

        assert KubernetesApp(
            name="valid-name",
            config=config,
            handlers=handlers,
            app=app_values,
            namespace="test-namespace",
        )
