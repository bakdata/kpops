from kpops.component_handlers.helm_wrapper.helm_diff import HelmDiff
from kpops.component_handlers.helm_wrapper.model import HelmDiffConfig, HelmTemplate
from kpops.utils.dict_differ import Change


def test_diff():
    helm_diff = HelmDiff(HelmDiffConfig())
    templates = [HelmTemplate("a.yaml", {})]
    assert list(helm_diff.calc_changes(templates, templates)) == [
        Change(
            old_value={},
            new_value={},
        ),
    ]

    # test matching corresponding template files based on their filename
    assert list(
        helm_diff.calc_changes(
            [
                HelmTemplate("a.yaml", {"a": 1}),
                HelmTemplate("b.yaml", {"b": 1}),
            ],
            [
                HelmTemplate("a.yaml", {"a": 2}),
                HelmTemplate("c.yaml", {"c": 1}),
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

    # test no current release
    assert list(helm_diff.calc_changes((), [HelmTemplate("a.yaml", {"a": 1})])) == [
        Change(
            old_value={},
            new_value={"a": 1},
        ),
    ]
