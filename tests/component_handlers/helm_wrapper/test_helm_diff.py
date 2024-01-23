from pathlib import Path

import pytest

from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate
from kpops.component_handlers.kubernetes.model import KubernetesManifest
from kpops.utils.dict_differ import Change


class TestHelmDiff:
    @pytest.fixture()
    def helm_diff(self) -> HelmDiff:
        return HelmDiff(HelmDiffConfig())

    def test_calculate_changes_unchanged(self, helm_diff: HelmDiff):
        templates = [HelmTemplate(Path("a.yaml"), KubernetesManifest())]
        assert list(helm_diff.calculate_changes(templates, templates)) == [
            Change(
                old_value={},
                new_value={},
            ),
        ]

    def test_calculate_changes_matching(self, helm_diff: HelmDiff):
        # test matching corresponding template files based on their filename
        assert list(
            helm_diff.calculate_changes(
                [
                    HelmTemplate(Path("a.yaml"), KubernetesManifest({"a": 1})),
                    HelmTemplate(Path("b.yaml"), KubernetesManifest({"b": 1})),
                ],
                [
                    HelmTemplate(Path("a.yaml"), KubernetesManifest({"a": 2})),
                    HelmTemplate(Path("c.yaml"), KubernetesManifest({"c": 1})),
                ],
            )
        ) == [
            Change(
                old_value={"a": 1},
                new_value={"a": 2},
            ),
            Change(
                old_value={"b": 1},
                new_value={},
            ),
            Change(
                old_value={},
                new_value={"c": 1},
            ),
        ]

    def test_calculate_changes_new_release(self, helm_diff: HelmDiff):
        # test no current release
        assert list(
            helm_diff.calculate_changes(
                (), [HelmTemplate(Path("a.yaml"), KubernetesManifest({"a": 1}))]
            )
        ) == [
            Change(
                old_value={},
                new_value={"a": 1},
            ),
        ]
