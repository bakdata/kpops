from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from structlog.testing import capture_logs
from typing_extensions import override

from kpops.component_handlers.helm.helm import Helm
from kpops.component_handlers.helm.model import (
    HelmConfig,
    HelmRepoConfig,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.components.base_components.helm_app import HelmApp, HelmAppValues
from kpops.config import KpopsConfig, get_config, set_config
from kpops.manifests.kubernetes import K8S_LABEL_MAX_LEN
from kpops.utils.colorify import magentaify


@pytest.mark.usefixtures("mock_env")
class TestHelmApp:
    @pytest.fixture()
    def helm_mock(self, mocker: MockerFixture) -> MagicMock:
        helm_mock = mocker.MagicMock(Helm)
        mocker.patch(
            "kpops.components.base_components.helm_app.Helm", return_value=helm_mock
        )
        return helm_mock

    @pytest.fixture()
    def app_values(self) -> HelmAppValues:
        return HelmAppValues.model_validate({"foo": "test-value"})

    @pytest.fixture()
    def repo_config(self) -> HelmRepoConfig:
        return HelmRepoConfig(repository_name="test", url="https://bakdata.com")

    @pytest.fixture()
    def helm_app(
        self,
        app_values: HelmAppValues,
        repo_config: HelmRepoConfig,
    ) -> HelmApp:
        return HelmApp(
            name="test-helm-app",
            values=app_values,
            namespace="test-namespace",
            repo_config=repo_config,
        )

    async def test_should_lazy_load_helm_and_not_repo_add(
        self,
        helm_app: HelmApp,
        mocker: MockerFixture,
        helm_mock: MagicMock,
    ) -> None:
        helm_mock.add_repo.assert_not_called()

        mocker.patch.object(
            HelmApp,
            "helm_chart",
            return_value="test/test-chart",
            new_callable=mocker.PropertyMock,
        )

        await helm_app.deploy(False)

        helm_mock.upgrade_install.assert_called_once_with(
            "${pipeline.name}-test-helm-app",
            "test/test-chart",
            False,
            "test-namespace",
            {
                "nameOverride": "${pipeline.name}-test-helm-app",
                "fullnameOverride": "${pipeline.name}-test-helm-app",
                "foo": "test-value",
            },
            HelmUpgradeInstallFlags(),
        )

    async def test_should_lazy_load_helm_and_call_repo_add_when_implemented(
        self,
        helm_mock: MagicMock,
        mocker: MockerFixture,
        app_values: HelmAppValues,
    ) -> None:
        repo_config = HelmRepoConfig(
            repository_name="test-repo", url="https://test.com/charts/"
        )
        helm_app = HelmApp(
            name="test-helm-app",
            values=app_values,
            namespace="test-namespace",
            repo_config=repo_config,
            version="3.4.5",
        )

        mocker.patch.object(
            HelmApp,
            "helm_chart",
            return_value="test/test-chart",
            new_callable=mocker.PropertyMock,
        )

        await helm_app.deploy(dry_run=False)

        assert helm_mock.mock_calls == [
            mocker.call.add_repo(
                "test-repo",
                "https://test.com/charts/",
                RepoAuthFlags(),
            ),
            mocker.call.upgrade_install(
                "${pipeline.name}-test-helm-app",
                "test/test-chart",
                False,
                "test-namespace",
                {
                    "nameOverride": "${pipeline.name}-test-helm-app",
                    "fullnameOverride": "${pipeline.name}-test-helm-app",
                    "foo": "test-value",
                },
                HelmUpgradeInstallFlags(version="3.4.5"),
            ),
        ]

    async def test_should_deploy_app_with_local_helm_chart(
        self,
        helm_mock: MagicMock,
        app_values: HelmAppValues,
    ) -> None:
        class AppWithLocalChart(HelmApp):
            repo_config: None = None

            @property
            @override
            def helm_chart(self) -> str:
                return "path/to/helm/charts/"

        app_with_local_chart = AppWithLocalChart(
            name="test-app-with-local-chart",
            values=app_values,
            namespace="test-namespace",
        )

        await app_with_local_chart.deploy(dry_run=False)

        helm_mock.add_repo.assert_not_called()

        helm_mock.upgrade_install.assert_called_once_with(
            "${pipeline.name}-test-app-with-local-chart",
            "path/to/helm/charts/",
            False,
            "test-namespace",
            {
                "nameOverride": "${pipeline.name}-test-app-with-local-chart",
                "fullnameOverride": "${pipeline.name}-test-app-with-local-chart",
                "foo": "test-value",
            },
            HelmUpgradeInstallFlags(),
        )

    async def test_should_raise_not_implemented_error_when_helm_chart_is_not_set(
        self,
        helm_app: HelmApp,
        helm_mock: MagicMock,
    ) -> None:
        with pytest.raises(NotImplementedError) as error:
            await helm_app.deploy(True)
        helm_mock.add_repo.assert_called()
        assert (
            str(error.value)
            == "Please implement the helm_chart property of the kpops.components.base_components.helm_app module."
        )

    @pytest.mark.parametrize(
        "local_timeout, global_timeout, expected_timeout",
        [
            pytest.param(
                "30m", "10m", "30m", id="prioritize local over global timeout"
            ),
            pytest.param(
                None, "10m", "10m", id="prioritize global over default timeout"
            ),
            pytest.param(
                "30m", None, "30m", id="prioritize local over default timeout"
            ),
            pytest.param(None, None, "5m0s", id="fallback to default timeout"),
        ],
    )
    def test_should_apply_timeout_precedence(
        self,
        local_timeout: str | None,
        global_timeout: str | None,
        expected_timeout: str,
        app_values: HelmAppValues,
    ) -> None:
        original_config = get_config()
        set_config(
            KpopsConfig(
                kafka_brokers="broker:9092",
                helm_config=HelmConfig(timeout=global_timeout),
            )
        )
        try:
            helm_app = HelmApp(
                name="test-helm-app",
                values=app_values,
                namespace="test-namespace",
                timeout=local_timeout,
            )
            assert helm_app.deploy_flags.timeout == expected_timeout
        finally:
            set_config(original_config)

    def test_should_set_force_from_global_config(
        self,
        app_values: HelmAppValues,
    ) -> None:
        original_config = get_config()
        set_config(
            KpopsConfig(
                kafka_brokers="broker:9092",
                helm_config=HelmConfig(force_replace=True),
            )
        )
        try:
            helm_app = HelmApp(
                name="test-helm-app",
                values=app_values,
                namespace="test-namespace",
            )
            assert helm_app.deploy_flags.force is True
        finally:
            set_config(original_config)

    async def test_should_call_helm_uninstall_when_destroying_helm_app(
        self,
        helm_app: HelmApp,
        helm_mock: MagicMock,
    ) -> None:
        stdout = 'HelmApp - release "test-helm-app" uninstalled'
        helm_mock.uninstall.return_value = stdout

        with capture_logs() as cap_logs:
            await helm_app.destroy(True)

        helm_mock.uninstall.assert_called_once_with(
            "test-namespace", "${pipeline.name}-test-helm-app", True
        )

        assert {"event": magentaify(stdout), "log_level": "info"} in cap_logs

    async def test_should_call_helm_uninstall_when_resetting_helm_app(
        self,
        helm_app: HelmApp,
        helm_mock: MagicMock,
    ) -> None:
        stdout = 'HelmApp - release "test-helm-app" uninstalled'
        helm_mock.uninstall.return_value = stdout

        with capture_logs() as cap_logs:
            await helm_app.reset(True)

        helm_mock.uninstall.assert_called_once_with(
            "test-namespace", "${pipeline.name}-test-helm-app", True
        )

        assert {"event": magentaify(stdout), "log_level": "info"} in cap_logs

    async def test_should_call_helm_uninstall_when_cleaning_helm_app(
        self,
        helm_app: HelmApp,
        helm_mock: MagicMock,
    ) -> None:
        stdout = 'HelmApp - release "test-helm-app" uninstalled'
        helm_mock.uninstall.return_value = stdout

        with capture_logs() as cap_logs:
            await helm_app.clean(True)

        helm_mock.uninstall.assert_called_once_with(
            "test-namespace", "${pipeline.name}-test-helm-app", True
        )

        assert {"event": magentaify(stdout), "log_level": "info"} in cap_logs

    def test_helm_name_override(
        self,
        repo_config: HelmRepoConfig,
    ) -> None:
        helm_app = HelmApp(
            prefix="test-pipeline-prefix-with-a-long-name-",
            name="helm-app-name-is-very-long-as-well",
            values=HelmAppValues(),
            namespace="test-namespace",
            repo_config=repo_config,
        )
        assert (
            helm_app.to_helm_values()["nameOverride"]
            == "test-pipeline-prefix-with-a-long-name-helm-app-name-is-ve-3fbb7"
        )
        assert (
            helm_app.to_helm_values()["fullnameOverride"]
            == "test-pipeline-prefix-with-a-long-name-helm-app-name-is-ve-3fbb7"
        )
        assert len(helm_app.to_helm_values()["nameOverride"]) == K8S_LABEL_MAX_LEN
        assert len(helm_app.to_helm_values()["fullnameOverride"]) == K8S_LABEL_MAX_LEN
