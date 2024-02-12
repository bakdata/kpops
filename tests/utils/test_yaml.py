import pytest

from kpops.utils.yaml import substitute_nested


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
