from pathlib import Path
from unittest.mock import ANY, MagicMock

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

import kpops
from kpops.cli.main import app
from kpops.component_handlers.helm_wrapper.helm import Helm
from kpops.component_handlers.helm_wrapper.model import HelmConfig, Version
from kpops.component_handlers.kubernetes.model import KubernetesManifest

runner = CliRunner()

RESOURCE_PATH = Path(__file__).parent / "resources"


class TestManifest:
    @pytest.fixture()
    def mock_execute(self, mocker: MockerFixture) -> MagicMock:
        mock_execute = mocker.patch.object(Helm, "_Helm__execute")
        mock_execute.return_value = ""  # Helm Template
        return mock_execute

    @pytest.fixture()
    def mock_get_version(self, mocker: MockerFixture) -> MagicMock:
        mock_get_version = mocker.patch.object(Helm, "get_version")
        mock_get_version.return_value = Version(major=3, minor=12, patch=0)
        return mock_get_version

    @pytest.fixture(autouse=True)
    def helm(self, mock_get_version: MagicMock) -> Helm:
        return Helm(helm_config=HelmConfig())

    def test_default_config(self, mock_execute: MagicMock):
        result = runner.invoke(
            app,
            [
                "manifest",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )
        mock_execute.assert_called_with(
            [
                "helm",
                "template",
                "resources-custom-config-app2",
                "bakdata-streams-bootstrap/streams-app",
                "--namespace",
                "development-namespace",
                "--values",
                ANY,
                "--version",
                "2.9.0",
                "--timeout",
                "5m0s",
                "--wait",
            ],
        )
        assert result.exit_code == 0, result.stdout

    def test_custom_config(self, mock_execute: MagicMock):
        result = runner.invoke(
            app,
            [
                "manifest",
                str(RESOURCE_PATH / "custom-config/pipeline.yaml"),
                "--defaults",
                str(RESOURCE_PATH / "no-topics-defaults"),
                "--config",
                str(RESOURCE_PATH / "custom-config"),
                "--environment",
                "development",
            ],
            catch_exceptions=False,
        )
        mock_execute.assert_called_with(
            [
                "helm",
                "template",
                "resources-custom-config-app2",
                "bakdata-streams-bootstrap/streams-app",
                "--namespace",
                "development-namespace",
                "--values",
                ANY,
                "--version",
                "2.9.0",
                "--timeout",
                "5m0s",
                "--wait",
                "--api-versions",
                "2.1.1",
            ],
        )
        assert result.exit_code == 0, result.stdout

    def test_python_api(self):
        steps = kpops.manifest(
            RESOURCE_PATH / "custom-config/pipeline.yaml",
            defaults=RESOURCE_PATH / "no-topics-defaults",
            output=False,
            environment="development",
        )
        assert len(steps) == 2
        manifests = steps[0]
        assert len(manifests) == 1
        assert isinstance(manifests[0], KubernetesManifest)
        assert manifests[0] == {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "labels": {
                    "app": "resources-custom-config-app1",
                    "chart": "producer-app-2.9.0",
                    "release": "resources-custom-config-app1",
                },
                "name": "resources-custom-config-app1",
            },
            "spec": {
                "backoffLimit": 6,
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "resources-custom-config-app1",
                            "release": "resources-custom-config-app1",
                        }
                    },
                    "spec": {
                        "affinity": None,
                        "containers": [
                            {
                                "env": [
                                    {"name": "ENV_PREFIX", "value": "APP_"},
                                    {
                                        "name": "APP_BROKERS",
                                        "value": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                                    },
                                    {
                                        "name": "APP_SCHEMA_REGISTRY_URL",
                                        "value": "http://localhost:8081/",
                                    },
                                    {"name": "APP_DEBUG", "value": "false"},
                                    {
                                        "name": "APP_OUTPUT_TOPIC",
                                        "value": "resources-custom-config-app1",
                                    },
                                    {
                                        "name": "JAVA_TOOL_OPTIONS",
                                        "value": "-XX:MaxRAMPercentage=75.0 ",
                                    },
                                ],
                                "image": "producerApp:latest",
                                "imagePullPolicy": "Always",
                                "name": "resources-custom-config-app1",
                                "resources": {
                                    "limits": {"cpu": "500m", "memory": "2G"},
                                    "requests": {"cpu": "200m", "memory": "2G"},
                                },
                            }
                        ],
                        "restartPolicy": "OnFailure",
                    },
                },
            },
        }

        manifests = steps[1]
        assert len(manifests) == 2
        assert all(isinstance(manifest, KubernetesManifest) for manifest in manifests)
        assert manifests[0] == {
            "apiVersion": "v1",
            "data": {
                "jmx-kafka-streams-app-prometheus.yml": "jmxUrl: "
                "service:jmx:rmi:///jndi/rmi://localhost:5555/jmxrmi\n"
                "lowercaseOutputName: true\n"
                "lowercaseOutputLabelNames: "
                "true\n"
                "ssl: false\n"
                "rules:\n"
                '  - pattern: ".*"\n'
            },
            "kind": "ConfigMap",
            "metadata": {
                "labels": {
                    "app": "resources-custom-config-app2",
                    "chart": "streams-app-2.9.0",
                    "heritage": "Helm",
                    "release": "resources-custom-config-app2",
                },
                "name": "resources-custom-config-app2-jmx-configmap",
            },
        }
        assert manifests[1] == {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "labels": {
                    "app": "resources-custom-config-app2",
                    "chart": "streams-app-2.9.0",
                    "pipeline": "resources-custom-config",
                    "release": "resources-custom-config-app2",
                },
                "name": "resources-custom-config-app2",
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": "resources-custom-config-app2",
                        "release": "resources-custom-config-app2",
                    }
                },
                "template": {
                    "metadata": {
                        "annotations": {
                            "prometheus.io/port": "5556",
                            "prometheus.io/scrape": "true",
                        },
                        "labels": {
                            "app": "resources-custom-config-app2",
                            "pipeline": "resources-custom-config",
                            "release": "resources-custom-config-app2",
                        },
                    },
                    "spec": {
                        "affinity": {
                            "podAntiAffinity": {
                                "preferredDuringSchedulingIgnoredDuringExecution": [
                                    {
                                        "podAffinityTerm": {
                                            "labelSelector": {
                                                "matchExpressions": [
                                                    {
                                                        "key": "app",
                                                        "operator": "In",
                                                        "values": [
                                                            "resources-custom-config-app2"
                                                        ],
                                                    }
                                                ]
                                            },
                                            "topologyKey": "kubernetes.io/hostname",
                                        },
                                        "weight": 1,
                                    }
                                ]
                            }
                        },
                        "containers": [
                            {
                                "env": [
                                    {"name": "ENV_PREFIX", "value": "APP_"},
                                    {"name": "KAFKA_JMX_PORT", "value": "5555"},
                                    {
                                        "name": "APP_VOLATILE_GROUP_INSTANCE_ID",
                                        "value": "true",
                                    },
                                    {
                                        "name": "APP_BROKERS",
                                        "value": "http://k8kafka-cp-kafka-headless.kpops.svc.cluster.local:9092",
                                    },
                                    {
                                        "name": "APP_SCHEMA_REGISTRY_URL",
                                        "value": "http://localhost:8081/",
                                    },
                                    {"name": "APP_DEBUG", "value": "false"},
                                    {
                                        "name": "APP_INPUT_TOPICS",
                                        "value": "resources-custom-config-app1",
                                    },
                                    {
                                        "name": "APP_OUTPUT_TOPIC",
                                        "value": "resources-custom-config-app2",
                                    },
                                    {
                                        "name": "APP_ERROR_TOPIC",
                                        "value": "resources-custom-config-app2-error",
                                    },
                                    {
                                        "name": "JAVA_TOOL_OPTIONS",
                                        "value": "-Dcom.sun.management.jmxremote.port=5555 "
                                        "-Dcom.sun.management.jmxremote.authenticate=false "
                                        "-Dcom.sun.management.jmxremote.ssl=false "
                                        "-XX:MaxRAMPercentage=75.0 ",
                                    },
                                ],
                                "image": "some-image:latest",
                                "imagePullPolicy": "Always",
                                "name": "resources-custom-config-app2",
                                "ports": [{"containerPort": 5555, "name": "jmx"}],
                                "resources": {
                                    "limits": {"cpu": "500m", "memory": "2G"},
                                    "requests": {"cpu": "200m", "memory": "300Mi"},
                                },
                            },
                            {
                                "command": [
                                    "java",
                                    "-XX:+UnlockExperimentalVMOptions",
                                    "-XX:+UseCGroupMemoryLimitForHeap",
                                    "-XX:MaxRAMFraction=1",
                                    "-XshowSettings:vm",
                                    "-jar",
                                    "jmx_prometheus_httpserver.jar",
                                    "5556",
                                    "/etc/jmx-streams-app/jmx-kafka-streams-app-prometheus.yml",
                                ],
                                "image": "solsson/kafka-prometheus-jmx-exporter@sha256:6f82e2b0464f50da8104acd7363fb9b995001ddff77d248379f8788e78946143",
                                "name": "prometheus-jmx-exporter",
                                "ports": [{"containerPort": 5556}],
                                "resources": {
                                    "limits": {"cpu": "300m", "memory": "2G"},
                                    "requests": {"cpu": "100m", "memory": "500Mi"},
                                },
                                "volumeMounts": [
                                    {
                                        "mountPath": "/etc/jmx-streams-app",
                                        "name": "jmx-config",
                                    }
                                ],
                            },
                        ],
                        "volumes": [
                            {
                                "configMap": {
                                    "name": "resources-custom-config-app2-jmx-configmap"
                                },
                                "name": "jmx-config",
                            }
                        ],
                    },
                },
            },
        }
