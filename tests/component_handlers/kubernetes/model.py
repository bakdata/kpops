from textwrap import dedent

from kpops.component_handlers.kubernetes.model import KubernetesManifest


class TestKubernetesManifest:
    def test_from_yaml(self):
        helm_template = dedent(
            """
            ---
            # Source: chart/templates/test2.yaml
            apiVersion: v1
            kind: ServiceAccount
            metadata:
                labels:
                    foo: bar
            """
        )

        manifest = KubernetesManifest.from_yaml(helm_template)
        assert manifest == {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {"labels": {"foo": "bar"}},
        }
