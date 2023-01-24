from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from kpops.component_handlers.helm_wrapper.exception import ReleaseNotFoundException
from kpops.component_handlers.helm_wrapper.helm import Helm, HelmTemplate
from kpops.component_handlers.helm_wrapper.model import (
    HelmConfig,
    HelmUpgradeInstallFlags,
    RepoAuthFlags,
)
from kpops.components.streams_bootstrap.app_type import AppType

DEFAULTS_PATH = Path(__file__).parent / "resources"


class TestHelmWrapper:
    @pytest.fixture(autouse=True)
    def temp_file_mock(self, mocker: MockerFixture) -> MagicMock:
        temp_file_mock = mocker.patch("tempfile.NamedTemporaryFile")
        temp_file_mock.return_value.__enter__.return_value.name = "values.yaml"
        return temp_file_mock

    @pytest.fixture
    def run_command(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch.object(Helm, "_Helm__execute")

    @pytest.fixture
    def log_warning_mock(self, mocker: MockerFixture) -> MagicMock:
        return mocker.patch("kpops.component_handlers.helm_wrapper.helm.log.warning")

    def test_should_call_run_command_method_when_helm_install_with_defaults(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.upgrade_install(
            release_name="test-release",
            chart=f"bakdata-streams-bootstrap/{AppType.STREAMS_APP.value}",
            dry_run=False,
            namespace="test-namespace",
            values={"commandLine": "test"},
            flags=HelmUpgradeInstallFlags(),
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--install",
                "--timeout=5m0s",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--wait",
            ],
        )

    def test_should_include_configured_tls_parameters_on_add(
        self, run_command: MagicMock
    ):
        helm = Helm(HelmConfig())
        helm.add_repo(
            "test-repository",
            "fake",
            RepoAuthFlags(ca_file=Path("a_file.ca"), insecure_skip_tls_verify=True),
        )
        run_command.assert_has_calls(
            [
                mock.call(
                    [
                        "helm",
                        "repo",
                        "add",
                        "test-repository",
                        "fake",
                        "--ca-file",
                        "a_file.ca",
                        "--insecure-skip-tls-verify",
                    ],
                ),
                mock.call(
                    ["helm", "repo", "update"],
                ),
            ]
        )

    def test_should_include_configured_tls_parameters_on_update(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        helm_wrapper.upgrade_install(
            release_name="test-release",
            chart="test-repository/test-chart",
            dry_run=False,
            namespace="test-namespace",
            values={},
            flags=HelmUpgradeInstallFlags(
                repo_auth_flags=RepoAuthFlags(
                    ca_file=Path("a_file.ca"), insecure_skip_tls_verify=True
                )
            ),
        )

        run_command.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "test-repository/test-chart",
                "--install",
                "--timeout=5m0s",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--ca-file",
                "a_file.ca",
                "--insecure-skip-tls-verify",
                "--wait",
            ],
        )

    def test_should_call_run_command_method_when_helm_install_with_non_defaults(
        self,
        run_command: MagicMock,
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        helm_wrapper.upgrade_install(
            release_name="test-release",
            chart="test-repository/streams-app",
            namespace="test-namespace",
            dry_run=True,
            values={"commandLine": "test"},
            flags=HelmUpgradeInstallFlags(
                force=True,
                timeout="120s",
                wait=True,
                wait_for_jobs=True,
                version="2.4.2",
            ),
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "upgrade",
                "test-release",
                "test-repository/streams-app",
                "--install",
                "--timeout=120s",
                "--namespace",
                "test-namespace",
                "--values",
                "values.yaml",
                "--dry-run",
                "--force",
                "--wait",
                "--wait-for-jobs",
                "--version",
                "2.4.2",
            ],
        )

    def test_should_call_run_command_method_when_uninstalling_streams_app(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        helm_wrapper.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
        )
        run_command.assert_called_once_with(
            ["helm", "uninstall", "test-release", "--namespace", "test-namespace"],
        )

    def test_should_log_warning_when_release_not_found(
        self, run_command: MagicMock, log_warning_mock: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())
        run_command.side_effect = ReleaseNotFoundException()
        helm_wrapper.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=False,
        )

        log_warning_mock.assert_called_once_with(
            "Release with name test-release not found. Could not uninstall app."
        )

    def test_should_call_run_command_method_when_installing_streams_app__with_dry_run(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.uninstall(
            namespace="test-namespace",
            release_name="test-release",
            dry_run=True,
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "uninstall",
                "test-release",
                "--namespace",
                "test-namespace",
                "--dry-run",
            ],
        )

    def test_validate_console_output(self):
        with pytest.raises(RuntimeError):
            Helm.parse_helm_command_stderr_output(
                "A specific\n eRrOr was found in this line"
            )
        with pytest.raises(ReleaseNotFoundException):
            Helm.parse_helm_command_stderr_output("New \nmessage\n ReLease: noT foUnD")
        try:
            Helm.parse_helm_command_stderr_output("This is \njust WaRnIng nothing more")
        except RuntimeError as e:
            pytest.fail(
                f"validate_console_output() raised RuntimeError unexpectedly!\nError message: {e}"
            )
        try:
            Helm.parse_helm_command_stderr_output("This is \njust WaRnIng nothing more")
        except ReleaseNotFoundException:
            pytest.fail(
                f"validate_console_output() raised ReleaseNotFoundException unexpectedly!\nError message: {ReleaseNotFoundException}"
            )

    def test_load_manifest(self):
        stdout = """---
# Resource: chart/templates/test1.yaml
"""
        with pytest.raises(ValueError):
            helm_templates = list(Helm.load_helm_manifest(stdout))
            assert len(helm_templates) == 0

        stdout = """---
# Source: chart/templates/test2.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
    labels:
        foo: bar
"""

        helm_template = HelmTemplate.load("test2.yaml", stdout)
        assert helm_template.filepath == "test2.yaml"
        assert helm_template.template == {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"labels": {"foo": "bar"}},
        }

        helm_templates = list(Helm.load_helm_manifest(stdout))
        assert len(helm_templates) == 1
        helm_template = helm_templates[0]
        assert isinstance(helm_template, HelmTemplate)
        assert helm_template.filepath == "chart/templates/test2.yaml"
        assert helm_template.template == {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"labels": {"foo": "bar"}},
        }

        stdout = """---
# Source: chart/templates/test3a.yaml
data:
    - a: 1
    - b: 2
---
# Source: chart/templates/test3b.yaml
foo: bar
"""
        helm_templates = list(Helm.load_helm_manifest(stdout))
        assert len(helm_templates) == 2
        assert all(
            isinstance(helm_template, HelmTemplate) for helm_template in helm_templates
        )
        assert helm_templates[0].filepath == "chart/templates/test3a.yaml"
        assert helm_templates[0].template == {"data": [{"a": 1}, {"b": 2}]}
        assert helm_templates[1].filepath == "chart/templates/test3b.yaml"
        assert helm_templates[1].template == {"foo": "bar"}

        stdout = """Release "test" has been upgraded. Happy Helming!
NAME: test
LAST DEPLOYED: Wed Nov 23 16:37:17 2022
NAMESPACE: test-namespace
STATUS: pending-upgrade
REVISION: 8
TEST SUITE: None
HOOKS:
MANIFEST:
---
# Source: chart/templates/test3a.yaml
data:
    - a: 1
    - b: 2
---
# Source: chart/templates/test3b.yaml
foo: bar
"""
        helm_templates = list(Helm.load_helm_manifest(stdout))
        assert len(helm_templates) == 2
        assert all(
            isinstance(helm_template, HelmTemplate) for helm_template in helm_templates
        )
        assert helm_templates[0].filepath == "chart/templates/test3a.yaml"
        assert helm_templates[0].template == {"data": [{"a": 1}, {"b": 2}]}
        assert helm_templates[1].filepath == "chart/templates/test3b.yaml"
        assert helm_templates[1].template == {"foo": "bar"}

    def test_get_manifest(self, run_command: MagicMock):
        helm_wrapper = Helm(helm_config=HelmConfig())
        run_command.return_value = """Release "test-release" has been upgraded. Happy Helming!
NAME: test-release
---
# Source: chart/templates/test.yaml
data:
    - a: 1
    - b: 2
"""
        helm_templates = list(
            helm_wrapper.get_manifest("test-release", "test-namespace")
        )
        run_command.assert_called_once_with(
            command=[
                "helm",
                "get",
                "manifest",
                "test-release",
                "--namespace",
                "test-namespace",
            ],
        )
        assert len(helm_templates) == 1
        assert helm_templates[0].filepath == "chart/templates/test.yaml"
        assert helm_templates[0].template == {"data": [{"a": 1}, {"b": 2}]}

        run_command.side_effect = ReleaseNotFoundException()
        assert helm_wrapper.get_manifest("test-release", "test-namespace") == ()

    def test_should_call_run_command_method_when_helm_template_with_api_versions(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.template(
            release_name="test-release",
            chart="bakdata-streams-bootstrap/streams-app",
            api_versions="2.1.1",
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "template",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
                "--api-versions" "2.1.1",
            ],
        )

    def test_should_call_run_command_method_when_helm_template_without_api_versions(
        self, run_command: MagicMock
    ):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.template(
            release_name="test-release",
            chart="bakdata-streams-bootstrap/streams-app",
        )
        run_command.assert_called_once_with(
            [
                "helm",
                "template",
                "test-release",
                "bakdata-streams-bootstrap/streams-app",
            ],
        )

    def test_helm_template_without_api_versions(self, run_command: MagicMock):
        helm_wrapper = Helm(helm_config=HelmConfig())

        helm_wrapper.template(
            release_name="test-release",
            chart="bakdata-streams-bootstrap/streams-app",
        )

        run_command.return_value = """
---
# Source: streams-app/templates/jmx-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bakdata-streams-app-jmx-configmap
  labels:
    app: bakdata-streams-app
    chart: streams-app-0.1.0
    release: stream-bootstrap
    heritage: Helm
data:
  jmx-kafka-streams-app-prometheus.yml: |+
    jmxUrl: service:jmx:rmi:///jndi/rmi://localhost:5555/jmxrmi
    lowercaseOutputName: true
    lowercaseOutputLabelNames: true
    ssl: false
    rules:
      - pattern: ".*"
---
# Source: streams-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bakdata-streams-app
  labels:
    app: bakdata-streams-app
    chart: streams-app-0.1.0
    release: stream-bootstrap
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bakdata-streams-app
      release: stream-bootstrap
  template:
    metadata:
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "5556"
      labels:
        app: bakdata-streams-app
        release: stream-bootstrap
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 1
            podAffinityTerm:
              topologyKey: "kubernetes.io/hostname"
              labelSelector:
                matchExpressions:
                  - key: app
                    operator: In
                    values:
                      - bakdata-streams-app
      containers:
        - name: bakdata-streams-app
          image: "streamsApp:latest"
          imagePullPolicy: "Always"
          resources:
            limits:
              cpu: 500m
              memory: 2G
            requests:
              cpu: 200m
              memory: 300Mi
          env:
            - name: ENV_PREFIX
              value: APP_
            - name: KAFKA_JMX_PORT
              value: "5555"
            - name: "APP_BROKERS"
              value:
            - name: "APP_SCHEMA_REGISTRY_URL"
              value:
            - name: "APP_DEBUG"
              value: "false"
            - name: "APP_INPUT_TOPICS"
              value: ""
            - name: JAVA_TOOL_OPTIONS
              value: '-Dcom.sun.management.jmxremote.port=5555
                -Dcom.sun.management.jmxremote.authenticate=false
                -Dcom.sun.management.jmxremote.ssl=false
                -XX:MaxRAMPercentage=75.0
                '
          ports:
            - containerPort: 5555
              name: jmx
        - name: prometheus-jmx-exporter
          image: "solsson/kafka-prometheus-jmx-exporter@sha256:6f82e2b0464f50da8104acd7363fb9b995001ddff77d248379f8788e78946143"
          command:
            - java
            - -XX:+UnlockExperimentalVMOptions
            - -XX:+UseCGroupMemoryLimitForHeap
            - -XX:MaxRAMFraction=1
            - -XshowSettings:vm
            - -jar
            - jmx_prometheus_httpserver.jar
            - "5556"
            - /etc/jmx-streams-app/jmx-kafka-streams-app-prometheus.yml
          ports:
            - containerPort: 5556
          resources:
            limits:
              cpu: 300m
              memory: 2G
            requests:
              cpu: 100m
              memory: 500Mi
          volumeMounts:
            - name: jmx-config
              mountPath: /etc/jmx-streams-app
      volumes:
        - name: jmx-config
          configMap:
            name: bakdata-streams-app-jmx-configmap
"""
