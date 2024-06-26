import pytest

from kpops.api.exception import ValidationError
from kpops.component_handlers.kubernetes.utils import validate_image_tag


def test_is_valid_image_tag():
    assert validate_image_tag("1.2.3") == "1.2.3"
    assert validate_image_tag("123") == "123"
    assert validate_image_tag("1_2_3") == "1_2_3"
    assert validate_image_tag("1-2-3") == "1-2-3"
    assert validate_image_tag("latest") == "latest"
    assert (
        validate_image_tag(
            "1ff6c18fbef2045af6b9c16bf034cc421a29027b800e4f9b68ae9b1cb3e9ae07"
        )
        == "1ff6c18fbef2045af6b9c16bf034cc421a29027b800e4f9b68ae9b1cb3e9ae07"
    )
    with pytest.raises(ValidationError):
        assert validate_image_tag("la!est") is False
