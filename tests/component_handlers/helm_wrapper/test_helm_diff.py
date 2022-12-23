from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate


def test_diff():
    helm_wrapper = HelmDiff(HelmDiffConfig())
    templates = [HelmTemplate("a.yaml", {})]
    assert helm_wrapper.get_diff(templates, templates) == [
        (
            {},
            {},
        ),
    ]

    # test matching corresponding template files based on their filename
    assert helm_wrapper.get_diff(
        [
            HelmTemplate("a.yaml", {"a": 1}),
            HelmTemplate("b.yaml", {"b": 1}),
        ],
        [
            HelmTemplate("a.yaml", {"a": 2}),
            HelmTemplate("c.yaml", {"c": 1}),
        ],
    ) == [
        (
            {"a": 1},
            {"a": 2},
        ),
        (
            {"b": 1},
            {},
        ),
        (
            {},
            {"c": 1},
        ),
    ]

    # test no current release
    assert helm_wrapper.get_diff((), [HelmTemplate("a.yaml", {"a": 1})]) == [
        (
            {},
            {"a": 1},
        ),
    ]
