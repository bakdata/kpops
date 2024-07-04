from kpops.component_handlers.kubernetes.utils import is_valid_image_tag

MAX_LENGTH = 128


def test_validate_image_tag_valid():
    valid_tags = [
        "valid-tag",
        "VALID_TAG",
        "valid.tag",
        "valid-tag_123",
        "v" * MAX_LENGTH,
    ]
    for tag in valid_tags:
        assert is_valid_image_tag(tag) is True


def test_if_image_tag_is_invalid():
    invalid_tags = [
        "invalid tag!",
        "",
        " " * (MAX_LENGTH + 1),
        "a" * (MAX_LENGTH + 1),
        "@invalid",
    ]
    for tag in invalid_tags:
        assert is_valid_image_tag(tag) is False
