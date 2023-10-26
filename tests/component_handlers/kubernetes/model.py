from textwrap import dedent

import pytest

from kpops.component_handlers.kubernetes.model import KubernetesManifest


class TestKubernetesManifest:
    @pytest.mark.parametrize(
        ("helm_template", "expected_manifest"),
        [
            pytest.param(
                dedent(
                    """
                    ---
                    # Source: chart/templates/test2.yaml
                    apiVersion: v1
                    kind: ServiceAccount
                    metadata:
                        labels:
                            foo: bar
                    """
                ),
                KubernetesManifest(
                    {
                        "apiVersion": "v1",
                        "kind": "ServiceAccount",
                        "metadata": {"labels": {"foo": "bar"}},
                    }
                ),
            )
        ],
    )
    def test_from_yaml(self, helm_template: str, expected_manifest: KubernetesManifest):
        assert KubernetesManifest.from_yaml(helm_template) == expected_manifest
