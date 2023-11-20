from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from typing_extensions import override

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.components.base_components.kubernetes_app import (
    KubernetesApp,
    KubernetesAppConfig,
)
from kpops.utils.colorify import magentaify

DEFAULTS_PATH = Path(__file__).parent / "resources"


class KubernetesTestValue(KubernetesAppConfig):
    fullname_override: str


class TestKubernetesApp:
    @pytest.fixture()
    def config(self) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            helm_diff_config=HelmDiffConfig(),
        )

    @pytest.fixture()
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    @pytest.fixture()
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.kubernetes_app.Helm"
        ).return_value

    @pytest.fixture()
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.components.base_components.kubernetes_app.log.info")

    @pytest.fixture()
    def app_value(self) -> KubernetesTestValue:
        return KubernetesTestValue(**{"fullname_override": "test-value"})

    @pytest.fixture()
    def repo_config(self) -> HelmRepoConfig:
        return HelmRepoConfig(repository_name="test", url="https://bakdata.com")

    @pytest.fixture()
    def kubernetes_app(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        app_value: KubernetesTestValue,
        repo_config: HelmRepoConfig,
    ) -> KubernetesApp:
        return KubernetesApp(
            name="test-kubernetes-app",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
            repo_config=repo_config,
        )

    def test_should_lazy_load_helm_wrapper_and_not_repo_add(
        self,
        kubernetes_app: KubernetesApp,
        mocker: MockerFixture,
        helm_mock: MagicMock,
    ):
        helm_mock.add_repo.assert_not_called()

        mocker.patch.object(
            KubernetesApp,
            "helm_chart",
            return_value="test/test-chart",
            new_callable=mocker.PropertyMock,
        )

        kubernetes_app.deploy(False)

        helm_mock.upgrade_install.assert_called_once_with(
            "${pipeline_name}-test-kubernetes-app",
            "test/test-chart",
            False,
            "test-namespace",
            {"fullnameOverride": "test-value"},
            HelmUpgradeInstallFlags(),
        )

    def test_should_lazy_load_helm_wrapper_and_call_repo_add_when_implemented(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        mocker: MockerFixture,
        app_value: KubernetesTestValue,
    ):
        repo_config = HelmRepoConfig(
            repository_name="test-repo", url="https://test.com/charts/"
        )
        kubernetes_app = KubernetesApp(
            name="test-kubernetes-app",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
            repo_config=repo_config,
            version="3.4.5",
        )

        mocker.patch.object(
            KubernetesApp,
            "helm_chart",
            return_value="test/test-chart",
            new_callable=mocker.PropertyMock,
        )

        kubernetes_app.deploy(dry_run=False)

        assert helm_mock.mock_calls == [
            mocker.call.add_repo(
                "test-repo",
                "https://test.com/charts/",
                RepoAuthFlags(),
            ),
            mocker.call.upgrade_install(
                "${pipeline_name}-test-kubernetes-app",
                "test/test-chart",
                False,
                "test-namespace",
                {"fullnameOverride": "test-value"},
                HelmUpgradeInstallFlags(version="3.4.5"),
            ),
        ]

    def test_should_deploy_app_with_local_helm_chart(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        app_value: KubernetesTestValue,
    ):
        class AppWithLocalChart(KubernetesApp):
            repo_config: None = None

            @property
            @override
            def helm_chart(self) -> str:
                return "path/to/helm/charts/"

        app_with_local_chart = AppWithLocalChart(
            name="test-app-with-local-chart",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )

        app_with_local_chart.deploy(dry_run=False)

        helm_mock.add_repo.assert_not_called()

        helm_mock.upgrade_install.assert_called_once_with(
            "${pipeline_name}-test-app-with-local-chart",
            "path/to/helm/charts/",
            False,
            "test-namespace",
            {"fullnameOverride": "test-value"},
            HelmUpgradeInstallFlags(),
        )

    def test_should_raise_not_implemented_error_when_helm_chart_is_not_set(
        self,
        kubernetes_app: KubernetesApp,
        helm_mock: MagicMock,
    ):
        with pytest.raises(NotImplementedError) as error:
            kubernetes_app.deploy(True)
        helm_mock.add_repo.assert_called()
        assert (
            str(error.value)
            == "Please implement the helm_chart property of the kpops.components.base_components.kubernetes_app module."
        )

    def test_should_call_helm_uninstall_when_destroying_kubernetes_app(
        self,
        kubernetes_app: KubernetesApp,
        helm_mock: MagicMock,
        log_info_mock: MagicMock,
    ):
        stdout = 'KubernetesAppComponent - release "test-kubernetes-app" uninstalled'
        helm_mock.uninstall.return_value = stdout

        kubernetes_app.destroy(True)

        helm_mock.uninstall.assert_called_once_with(
            "test-namespace", "${pipeline_name}-test-kubernetes-app", True
        )

        log_info_mock.assert_called_once_with(magentaify(stdout))

    def test_should_raise_value_error_when_name_is_not_valid(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        app_value: KubernetesTestValue,
        repo_config: HelmRepoConfig,
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
                repo_config=repo_config,
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
                repo_config=repo_config,
            )

        assert KubernetesApp(
            name="valid-name",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
            repo_config=repo_config,
        )
