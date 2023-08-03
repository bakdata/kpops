import pytest

from kpops.utils.pydantic import to_dash


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        ("BaseDefaultsComponent", "base-defaults-component"),
        ("ACRONYM", "acronym"),
        ("ACRONYMComponent", "acronym-component"),
    ],
)
def test_to_dash(input: str, expected: str):
    assert to_dash(input) == expected
