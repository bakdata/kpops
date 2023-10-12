from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppConfig,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class KubernetesTestValue(KubernetesAppConfig):
    foo: str


class TestKubernetesApp:
    @pytest.fixture()
    def config(self) -> PipelineConfig:
        return PipelineConfig(defaults_path=DEFAULTS_PATH, environment="development")

    @pytest.fixture()
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    @pytest.fixture()
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.components.base_components.kubernetes_app.log.info")

    @pytest.fixture()
    def app_value(self) -> KubernetesTestValue:
        return KubernetesTestValue(foo="foo")

    @pytest.fixture()
    def kubernetes_app(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        app_value: KubernetesTestValue,
    ) -> KubernetesApp:
        return KubernetesApp(
            name="test-kubernetes-app",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )

    def test_should_raise_value_error_when_name_is_not_valid(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        app_value: KubernetesTestValue,
    ):
        with pytest.raises(
            ValueError, match=r"The component name .* is invalid for Kubernetes."
        ):
            KubernetesApp(
                name="Not-Compatible*",
                config=config,
                handlers=handlers,
                app=app_value,
                namespace="test-namespace",
            )

        with pytest.raises(
            ValueError, match=r"The component name .* is invalid for Kubernetes."
        ):
            KubernetesApp(
                name="snake_case*",
                config=config,
                handlers=handlers,
                app=app_value,
                namespace="test-namespace",
            )

        assert KubernetesApp(
            name="valid-name",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )
