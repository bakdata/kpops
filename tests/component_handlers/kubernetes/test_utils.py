import pytest

from kpops.component_handlers.kubernetes.utils import is_valid_image_tag

MAX_LENGTH = 128


@pytest.mark.parametrize(
    "tag",
    [
        "valid-tag",
        "VALID_TAG",
        "valid.tag",
        "valid-tag_123",
        "v" * MAX_LENGTH,
    ],
)
def test_validate_image_tag_valid(tag):
    assert is_valid_image_tag(tag) is True


@pytest.mark.parametrize(
    "tag",
    [
        "invalid tag!",
        "",
        " " * (MAX_LENGTH + 1),
        "a" * (MAX_LENGTH + 1),
        "@invalid",
    ],
)
def test_if_image_tag_is_invalid(tag):
    assert is_valid_image_tag(tag) is False
