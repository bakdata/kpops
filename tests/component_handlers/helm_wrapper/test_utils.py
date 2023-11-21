import hashlib

from kpops.component_handlers.helm_wrapper.utils import (
    create_helm_release_name,
)


def test_helm_release_name_for_long_names():
    long_release_name = "example-component-name-too-long-fake-fakefakefakefakefake"
    actual_release_name = (
        "example-component-name-too-long-fake-fakefakef-"
        + hashlib.sha1(long_release_name.encode("utf-8")).hexdigest()[:4]
    )
    expected_helm_release_name = create_helm_release_name(long_release_name)

    assert expected_helm_release_name == actual_release_name
    assert len(expected_helm_release_name) < 53


def test_helm_release_name_for_install_and_clean_must_be_different():
    long_release_name = "example-component-name-too-long-fake-fakefakefakefakefake"
    long_clean_release_name = (
        "example-component-name-too-long-fake-fakefakefakefakefake-clean"
    )
    expected_helm_release_name = create_helm_release_name(long_release_name)
    expected_helm_clean_release_name = create_helm_release_name(long_clean_release_name)

    assert expected_helm_release_name != expected_helm_clean_release_name


def test_helm_release_name_for_short_names():
    short_release_name = "example-component-name"
    expected_helm_release_name = create_helm_release_name(short_release_name)
    assert expected_helm_release_name == short_release_name
    assert len(expected_helm_release_name) < 53
