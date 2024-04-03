from kpops.component_handlers.helm_wrapper.utils import (
    create_helm_release_name,
)


def test_helm_release_name_for_long_names():
    long_release_name = "example-component-name-too-long-fake-fakefakefakefakefake"

    actual_release_name = create_helm_release_name(long_release_name)

    expected_helm_release_name = "example-component-name-too-long-fake-fakefakefa-0a7fc"
    assert expected_helm_release_name == actual_release_name
    assert len(expected_helm_release_name) == 53


def test_helm_release_name_for_install_and_clean_must_be_different():
    long_release_name = "example-component-name-too-long-fake-fakefakefakefakefake"

    helm_clean_release_name = create_helm_release_name(long_release_name, "-clean")
    expected_helm_release_name = (
        "example-component-name-too-long-fake-fakefakef-0a7fc-clean"
    )

    assert expected_helm_release_name != helm_clean_release_name


def test_helm_release_name_for_short_names():
    short_release_name = "example-component-name"

    actual_helm_release_name = create_helm_release_name(short_release_name)

    assert actual_helm_release_name == short_release_name
    assert len(actual_helm_release_name) <= 53
