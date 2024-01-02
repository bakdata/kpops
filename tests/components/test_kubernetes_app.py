from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers import ComponentHandlers
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppValues,
)
from kpops.config import KpopsConfig

DEFAULTS_PATH = Path(__file__).parent / "resources"


class KubernetesTestValue(KubernetesAppValues):
    foo: str


class TestKubernetesApp:
    @pytest.fixture()
    def config(self) -> KpopsConfig:
        return KpopsConfig(defaults_path=DEFAULTS_PATH)

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
    def app_values(self) -> KubernetesTestValue:
        return KubernetesTestValue(foo="foo")

    @pytest.fixture()
    def kubernetes_app(
        self,
        config: KpopsConfig,
        handlers: ComponentHandlers,
        app_values: KubernetesTestValue,
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
        app_values: KubernetesTestValue,
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
