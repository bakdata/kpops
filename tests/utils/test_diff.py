from typing import Any

import pytest

from kpops.component_handlers.helm_wrapper.model import KeyPath
from kpops.utils.dict_differ import Change, Diff, DiffType, render_diff


@pytest.mark.parametrize(
    ("d1", "d2", "ignore", "output"),
    [
        pytest.param({}, {}, None, None),
        pytest.param({}, {}, [("a", "b")], None),
        pytest.param(
            {"a": 1, "b": 2, "c": 3},
            {"a": 2, "d": 1},
            None,
            "\x1b[31m- a: 1\n"
            "\x1b[0m\x1b[33m?    ^\n"
            "\x1b[0m\x1b[32m+ a: 2\n"
            "\x1b[0m\x1b[33m?    ^\n"
            "\x1b[0m\x1b[32m+ d: 1\n"
            "\x1b[0m\x1b[31m- b: 2\n"
            "\x1b[0m\x1b[31m- c: 3\n"
            "\x1b[0m",
        ),
        pytest.param(
            {"a": 1, "b": 2, "c": 3},
            {"a": 2, "d": 1},
            [("a")],
            "\x1b[32m+ d: 1\n\x1b[0m\x1b[31m- b: 2\n\x1b[0m\x1b[31m- c: 3\n\x1b[0m",
        ),
        pytest.param(
            {"a": {"a": 1, "b": 2, "c": 3}, "b": 2, "c": 3},
            {"a": {"a": 9, "b": 8}, "d": 1},
            [("a", "a")],
            "  a:\n"
            "\x1b[31m-   b: 2\n"
            "\x1b[0m\x1b[33m?      ^\n"
            "\x1b[0m\x1b[32m+   b: 8\n"
            "\x1b[0m\x1b[33m?      ^\n"
            "\x1b[0m\x1b[32m+ d: 1\n"
            "\x1b[0m\x1b[31m-   c: 3\n"
            "\x1b[0m\x1b[31m- b: 2\n"
            "\x1b[0m\x1b[31m- c: 3\n"
            "\x1b[0m",
        ),
        pytest.param(
            {"a": {"a.foo/bar": 1, "b": 2, "c": 3}, "b": 2, "c": 3},
            {"a": {"a.foo/bar": 9, "b": 8}, "d": 1},
            [("a", "a.foo/bar")],
            "  a:\n"
            "\x1b[31m-   b: 2\n"
            "\x1b[0m\x1b[33m?      ^\n"
            "\x1b[0m\x1b[32m+   b: 8\n"
            "\x1b[0m\x1b[33m?      ^\n"
            "\x1b[0m\x1b[32m+ d: 1\n"
            "\x1b[0m\x1b[31m-   c: 3\n"
            "\x1b[0m\x1b[31m- b: 2\n"
            "\x1b[0m\x1b[31m- c: 3\n"
            "\x1b[0m",
        ),
    ],
)
def test_render_diff(
    d1: dict[str, Any],
    d2: dict[str, Any],
    ignore: list[KeyPath] | None,
    output: str | None,
):
    assert render_diff(d1, d2, ignore) == output


@pytest.mark.parametrize(
    ("d1", "d2", "output"),
    [
        # Input 1
        ({}, {}, []),
        # Input 2
        ({"a": 1}, {"a": 1}, []),
        # Input 3
        ({"a": 1, "b": 2}, {"b": 2, "a": 1}, []),
        # Input 4
        (
            {"a": 1, "b": 2, "c": 3},
            {"a": 2, "d": 1},
            [
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a",
                    change=Change(old_value=1, new_value=2),
                ),
                Diff(
                    diff_type=DiffType.ADD,
                    key="d",
                    change=Change(old_value=None, new_value=1),
                ),
                Diff(
                    diff_type=DiffType.REMOVE,
                    key="b",
                    change=Change(old_value=2, new_value=None),
                ),
                Diff(
                    diff_type=DiffType.REMOVE,
                    key="c",
                    change=Change(old_value=3, new_value=None),
                ),
            ],
        ),
        # Input 5
        (
            {"a": {"a": 1, "b": 2, "c": 3}, "b": 2, "c": 3},
            {"a": {"a": 9, "b": 8}, "d": 1},
            [
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a.a",
                    change=Change(old_value=1, new_value=9),
                ),
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a.b",
                    change=Change(old_value=2, new_value=8),
                ),
                Diff(
                    diff_type=DiffType.REMOVE,
                    key="a.c",
                    change=Change(old_value=3, new_value=None),
                ),
                Diff(
                    diff_type=DiffType.ADD,
                    key="d",
                    change=Change(old_value=None, new_value=1),
                ),
                Diff(
                    diff_type=DiffType.REMOVE,
                    key="b",
                    change=Change(old_value=2, new_value=None),
                ),
                Diff(
                    diff_type=DiffType.REMOVE,
                    key="c",
                    change=Change(old_value=3, new_value=None),
                ),
            ],
        ),
        # Input 6
        (
            {"a": {"a": {"a": 3}, "c": 3}},
            {"a": {"a": 9, "b": {"a": 9}}},
            [
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a.a",
                    change=Change(old_value={"a": 3}, new_value=9),
                ),
                Diff(
                    diff_type=DiffType.ADD,
                    key="a.b",
                    change=Change(old_value=None, new_value={"a": 9}),
                ),
                Diff(
                    diff_type=DiffType.REMOVE,
                    key="a.c",
                    change=Change(old_value=3, new_value=None),
                ),
            ],
        ),
        # Input 7
        (
            {"a": {"a": {"a": {"a": 3}}}},
            {"a": {"a": {"a": {"a": 8}}}},
            [
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a.a.a.a",
                    change=Change(old_value=3, new_value=8),
                ),
            ],
        ),
        # Input 8
        (
            {"a": [1, 2, 3]},
            {"a": [1, "x", 5]},
            [
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a[1]",
                    change=Change(old_value=2, new_value="x"),
                ),
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a[2]",
                    change=Change(old_value=3, new_value=5),
                ),
            ],
        ),
        # Input 9
        (
            {"a.b": 1},
            {"a.b": 2},
            [
                Diff(
                    diff_type=DiffType.CHANGE,
                    key="a.b",
                    change=Change(old_value=1, new_value=2),
                )
            ],
        ),
    ],
)
def test_get_diff(d1: dict[str, Any], d2: dict[str, Any], output: list[Diff[Any, Any]]):
    assert list(Diff.from_dicts(d1, d2)) == output
