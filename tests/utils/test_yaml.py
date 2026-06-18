from collections.abc import Mapping
from textwrap import dedent
from typing import Any

import pytest

from kpops.utils.yaml import print_yaml, substitute_nested


@pytest.mark.parametrize(
    ("input", "substitution", "expected"),
    [
        pytest.param(
            '"a": "b", "${a}": "c", "a_${b}": "d", "e": "${a_${b}}"',
            {"a": "b", "${a}": "c", "a_${b}": "d", "e": "${a_${b}}"},
            '"a": "b", "b": "c", "a_c": "d", "e": "d"',
            id="requires-multiple-passes",
        ),
        pytest.param(
            "${a}, ${b}, ${c}, ${d}",
            {
                "a": "0",
                "b": "${a}",
                "c": "${b}",
                "d": "${a}",
            },
            "0, 0, 0, 0",
            id="chained-references",
        ),
    ],
)
def test_substitute_nested(input: str, substitution: dict[str, str], expected: str):
    assert substitute_nested(input, **substitution) == expected


@pytest.mark.parametrize(
    ("data", "expected_stdout"),
    [
        pytest.param(
            {"foo": "bar"},
            dedent(
                """\
                    ---
                    foo: bar

                    """
            ),
        ),
        pytest.param(
            {"foo": "bar\nbaz"},
            dedent(
                """\
                    ---
                    foo: |-
                      bar
                      baz

                    """
            ),
        ),
        pytest.param(
            {"foo": ["bar", "baz"]},
            dedent(
                """\
                    ---
                    foo:
                      - bar
                      - baz

                    """
            ),
        ),
    ],
)
def test_print_yaml(
    capsys: pytest.CaptureFixture[str],
    data: Mapping[str, Any] | str,
    expected_stdout: str,
):
    print_yaml(data)
    captured = capsys.readouterr()
    assert captured.out == expected_stdout
    assert not captured.err
