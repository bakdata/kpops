from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.cli.pipeline_config import PipelineConfig
from kpops.component_handlers import ComponentHandlers
from kpops.component_handlers.helm_wrapper.model import (
    HelmDiffConfig,
    HelmRepoConfig,
    HelmTemplate,
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
    name_override: str


class TestKubernetesApp:
    @pytest.fixture
    def config(self) -> PipelineConfig:
        return PipelineConfig(
            defaults_path=DEFAULTS_PATH,
            environment="development",
            helm_diff_config=HelmDiffConfig(enable=True),
        )

    @pytest.fixture
    def handlers(self) -> ComponentHandlers:
        return ComponentHandlers(
            schema_handler=MagicMock(),
            connector_handler=MagicMock(),
            topic_handler=MagicMock(),
        )

    @pytest.fixture
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch(
            "kpops.components.base_components.kubernetes_app.Helm"
        ).return_value

    @pytest.fixture
    def log_info_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.components.base_components.kubernetes_app.log.info")

    @pytest.fixture
    def app_value(self) -> KubernetesTestValue:
        return KubernetesTestValue(**{"name_override": "test-value"})

    def test_should_lazy_load_helm_wrapper_and_not_repo_add(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        mocker: MockerFixture,
        helm_mock: MagicMock,
        app_value: KubernetesTestValue,
    ):
        kubernetes_app = KubernetesApp(
            name="test-kubernetes-apps",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )

        mocker.patch.object(
            kubernetes_app, "get_helm_chart", return_value="test/test-chart"
        )

        kubernetes_app.deploy(True)

        helm_mock.add_repo.assert_not_called()

        helm_mock.upgrade_install.assert_called_once_with(
            "test-kubernetes-apps",
            "test/test-chart",
            True,
            "test-namespace",
            {"nameOverride": "test-value"},
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
        repo_config = HelmRepoConfig(repository_name="test-repo", url="mock://test")
        kubernetes_app = KubernetesApp(
            name="test-kubernetes-apps",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
            repo_config=repo_config,
            version="3.4.5",
        )

        mocker.patch.object(
            kubernetes_app,
            "get_helm_chart",
            return_value="test/test-chart",
            new_callable=mocker.PropertyMock,
        )

        kubernetes_app.deploy(True)

        helm_mock.assert_has_calls(
            [
                mocker.call.add_repo(
                    "test-repo",
                    "mock://test",
                    RepoAuthFlags(),
                ),
                mocker.call.upgrade_install(
                    "test-kubernetes-apps",
                    "test/test-chart",
                    True,
                    "test-namespace",
                    {"nameOverride": "test-value"},
                    HelmUpgradeInstallFlags(version="3.4.5"),
                ),
            ]
        )

    def test_should_print_helm_diff_after_install_when_dry_run_and_helm_diff_enabled(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        mocker: MockerFixture,
        log_info_mock: MagicMock,
        app_value: KubernetesTestValue,
    ):
        kubernetes_app = KubernetesApp(
            name="test-kubernetes-apps",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )
        mocker.patch.object(
            kubernetes_app, "get_helm_chart", return_value="test/test-chart"
        )
        mock_load_manifest = mocker.patch(
            "kpops.components.base_components.kubernetes_app.Helm.load_helm_manifest",
            return_value=iter([HelmTemplate("path.yaml", {"a": 1})]),
        )
        spy_helm_diff = mocker.spy(kubernetes_app, "print_helm_diff")

        kubernetes_app.deploy(dry_run=True)

        spy_helm_diff.assert_called_once()
        helm_mock.get_manifest.assert_called_once_with(
            "test-kubernetes-apps", "test-namespace"
        )
        mock_load_manifest.assert_called_once()
        assert log_info_mock.mock_calls == [
            mocker.call("Helm release test-kubernetes-apps does not exist"),
            mocker.call("\n\x1b[32m+ a: 1\n\x1b[0m"),
        ]

    def test_should_raise_not_implemented_error_when_helm_chart_is_not_set(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        app_value: KubernetesTestValue,
    ):
        kubernetes_app = KubernetesApp(
            name="test-kubernetes-apps",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )

        with pytest.raises(NotImplementedError) as error:
            kubernetes_app.deploy(True)
        assert (
            "Please implement the get_helm_chart() method of the kpops.components.base_components.kubernetes_app module."
            == str(error.value)
        )

    def test_should_call_helm_uninstall_when_destroying_kubernetes_app(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        helm_mock: MagicMock,
        log_info_mock: MagicMock,
        app_value: KubernetesTestValue,
    ):
        kubernetes_app = KubernetesApp(
            name="test-kubernetes-apps",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )

        stdout = 'KubernetesAppComponent - release "test-kubernetes-apps" uninstalled'
        helm_mock.uninstall.return_value = stdout

        kubernetes_app.destroy(True)

        helm_mock.uninstall.assert_called_once_with(
            "test-namespace", "test-kubernetes-apps", True
        )

        log_info_mock.assert_called_once_with(magentaify(stdout))

    def test_should_raise_value_error_when_name_is_not_valid(
        self,
        config: PipelineConfig,
        handlers: ComponentHandlers,
        app_value: KubernetesTestValue,
    ):
        assert KubernetesApp(
            name="example-component-with-very-long-name-longer-than-most-of-our-kubernetes-apps",
            config=config,
            handlers=handlers,
            app=app_value,
            namespace="test-namespace",
        )

        with pytest.raises(ValueError):
            assert KubernetesApp(
                name="Not-Compatible*",
                config=config,
                handlers=handlers,
            )

        with pytest.raises(ValueError):
            assert KubernetesApp(
                name="snake_case",
                config=config,
                handlers=handlers,
            )
