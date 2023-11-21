import hashlib

from kpops.component_handlers.helm_wrapper.utils import (
    create_helm_release_name,
)


def test_helm_release_name():
    long_release_name = (
        "example-component-name-too-long-fake-fakefakefakefakefake-clean"
    )
    actual_release_name = hashlib.sha1(long_release_name.encode("utf-8")).hexdigest()
    expected_helm_release_name = create_helm_release_name(long_release_name)
    assert expected_helm_release_name == actual_release_name
    assert len(expected_helm_release_name) < 52
