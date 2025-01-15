from textwrap import dedent

import pytest

from kpops.manifests.kubernetes import KubernetesManifest


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
                [
                    KubernetesManifest.model_validate(
                        {
                            "apiVersion": "v1",
                            "kind": "ServiceAccount",
                            "metadata": {"labels": {"foo": "bar"}},
                        }
                    )
                ],
            )
        ],
    )
    def test_from_yaml(self, helm_template: str, expected_manifest: KubernetesManifest):
        manifests = KubernetesManifest.from_yaml(helm_template)
        assert list(manifests) == expected_manifest
