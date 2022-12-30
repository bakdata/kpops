from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import HelmRepoConfig, RepoAuthFlags
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppConfig,
)

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestKubernetesApp:
    @pytest.fixture
    def config(self) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            pipeline_prefix="",
        )

    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    def test_should_lazy_load_helm_wrapper_and_not_repo_add(
        self, config: PipelineConfig, handlers: ComponentHandlers
    ):
        app_config = KubernetesAppConfig(namespace="test")

        kubernetes_app = KubernetesApp(
            _type="test",
            handlers=handlers,
            app=app_config,
            config=config,
            name="test-kubernetes-apps",
        )

        kubernetes_app.helm_wrapper

    def test_should_lazy_load_helm_wrapper_and_call_repo_add_when_implemented(
        self, config: PipelineConfig, handlers: ComponentHandlers, mocker: MockerFixture
    ):

        app_config = KubernetesAppConfig(namespace="test")

        kubernetes_app = KubernetesApp(
            _type="test",
            handlers=handlers,
            app=app_config,
            config=config,
            name="test-kubernetes-apps",
        )

        helm_repo_config_mock = mocker.patch.object(
            kubernetes_app, "get_helm_repo_config"
        )
        helm_repo_config_mock.return_value = HelmRepoConfig(
            repository_name="test-name", url="mock://test"
        )

        value = mocker.patch(
            "kpops.components.base_components.kubernetes_app.Helm"
        ).return_value

        kubernetes_app.helm_wrapper
        value.add_repo.assert_called_once_with(
            "test-name",
            "mock://test",
            RepoAuthFlags(),
        )

    def test_name_check(self, config: PipelineConfig, handlers: ComponentHandlers):
        app_config = KubernetesAppConfig(namespace="test")

        assert KubernetesApp(
            _type="test",
            handlers=handlers,
            app=app_config,
            config=config,
            name="example-component-with-very-long-name-longer-than-most-of-our-kubernetes-apps",
        )

        with pytest.raises(ValueError):
            assert KubernetesApp(
                _type="test",
                handlers=handlers,
                app=app_config,
                config=config,
                name="Not-Compatible*",
            )

        with pytest.raises(ValueError):
            assert KubernetesApp(
                _type="test",
                handlers=handlers,
                app=app_config,
                config=config,
                name="snake_case",
            )
