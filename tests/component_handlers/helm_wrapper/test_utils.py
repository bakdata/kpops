from kpops.component_handlers.helm_wrapper.utils import trim_release_name


def test_trim_release_name_with_suffix():
    name = trim_release_name(
        "example-component-name-too-long-fake-fakefakefakefakefake", suffix="-clean"
    )
    assert name == "example-component-name-too-long-fake-fakefakef-clean"
    assert len(name) == 52


def test_no_need_of_trim_release_name_with_suffix():
    name = trim_release_name("normal-name-with-no-need-of-trim", suffix="-clean")
    assert name == "normal-name-with-no-need-of-trim"
