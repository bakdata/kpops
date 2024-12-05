import logging
from pathlib import Path

import pytest
from pytest import LogCaptureFixture

from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate
from kpops.manifests.kubernetes import KubernetesManifest, ObjectMeta
from kpops.utils.dict_differ import Change

logger = logging.getLogger("TestHelmDiff")


class TestHelmDiff:
    @pytest.fixture()
    def helm_diff(self) -> HelmDiff:
        return HelmDiff(HelmDiffConfig())

    def test_calculate_changes_unchanged(self, helm_diff: HelmDiff):
        templates = [
            HelmTemplate(
                Path("a.yaml"),
                KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({}),
                    }
                ),
            )
        ]
        assert list(helm_diff.calculate_changes(templates, templates)) == [
            Change(
                old_value=KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({}),
                    }
                ),
                new_value=KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({}),
                    }
                ),
            ),
        ]

    def test_calculate_changes_matching(self, helm_diff: HelmDiff):
        # test matching corresponding template files based on their filename
        assert list(
            helm_diff.calculate_changes(
                [
                    HelmTemplate(
                        Path("a.yaml"),
                        KubernetesManifest.model_validate(
                            {
                                "apiVersion": "v1",
                                "kind": "Deployment",
                                "metadata": ObjectMeta.model_validate({"a": "1"}),
                            }
                        ),
                    ),
                    HelmTemplate(
                        Path("b.yaml"),
                        KubernetesManifest.model_validate(
                            {
                                "apiVersion": "v1",
                                "kind": "Deployment",
                                "metadata": ObjectMeta.model_validate({"b": "1"}),
                            }
                        ),
                    ),
                ],
                [
                    HelmTemplate(
                        Path("a.yaml"),
                        KubernetesManifest.model_validate(
                            {
                                "apiVersion": "v1",
                                "kind": "Deployment",
                                "metadata": ObjectMeta.model_validate({"a": "2"}),
                            }
                        ),
                    ),
                    HelmTemplate(
                        Path("c.yaml"),
                        KubernetesManifest.model_validate(
                            {
                                "apiVersion": "v1",
                                "kind": "Deployment",
                                "metadata": ObjectMeta.model_validate({"c": "1"}),
                            }
                        ),
                    ),
                ],
            )
        ) == [
            Change(
                old_value=KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({"a": "1"}),
                    }
                ),
                new_value=KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({"a": "2"}),
                    }
                ),
            ),
            Change(
                old_value=KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({"b": "1"}),
                    }
                ),
                new_value=None,
            ),
            Change(
                old_value=None,
                new_value=KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({"c": "1"}),
                    }
                ),
            ),
        ]

    def test_calculate_changes_new_release(self, helm_diff: HelmDiff):
        # test no current release
        assert list(
            helm_diff.calculate_changes(
                (),
                [
                    HelmTemplate(
                        Path("a.yaml"),
                        KubernetesManifest.model_validate(
                            {
                                "apiVersion": "v1",
                                "kind": "Deployment",
                                "metadata": ObjectMeta.model_validate({"a": "1"}),
                            }
                        ),
                    )
                ],
            )
        ) == [
            Change(
                old_value=None,
                new_value=KubernetesManifest.model_validate(
                    {
                        "apiVersion": "v1",
                        "kind": "Deployment",
                        "metadata": ObjectMeta.model_validate({"a": "1"}),
                    }
                ),
            ),
        ]

    def test_log_helm_diff(self, helm_diff: HelmDiff, caplog: LogCaptureFixture):
        helm_diff.log_helm_diff(
            logger,
            (),
            [
                HelmTemplate(
                    Path("a.yaml"),
                    KubernetesManifest.model_validate(
                        {
                            "apiVersion": "v1",
                            "kind": "Deployment",
                            "metadata": ObjectMeta.model_validate({"a": "1"}),
                        }
                    ),
                )
            ],
        )
        assert caplog.messages == [
            "\n"
            "\x1b[32m+ apiVersion: v1\n"
            "\x1b[0m\x1b[32m+ kind: Deployment\n"
            "\x1b[0m\x1b[32m+ metadata:\n"
            "\x1b[0m\x1b[32m+   a: '1'\n"
            "\x1b[0m"
        ]
