from kpops.component_handlers.helm_wrapper.utils import trim_release_name


def test_trim_release_name_with_suffix():
    name = trim_release_name(
        "example-component-name-too-long-fake-fakefakefakefakefake-clean",
        suffix="-clean",
    )
    assert name == "example-component-name-too-long-fake-fakefakef-clean"
    assert len(name) == 52


def test_trim_release_name_without_suffix():
    name = trim_release_name(
        "example-component-name-too-long-fake-fakefakefakefakefake"
    )
    assert name == "example-component-name-too-long-fake-fakefakefakefak"
    assert len(name) == 52


def test_no_trim_release_name():
    assert (
        trim_release_name("normal-name-with-no-need-of-trim-clean", suffix="-clean")
        == "normal-name-with-no-need-of-trim-clean"
    )
    assert (
        trim_release_name("normal-name-with-no-need-of-trim")
        == "normal-name-with-no-need-of-trim"
    )
