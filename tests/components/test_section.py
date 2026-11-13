from typing import Annotated

import pytest
from pydantic import computed_field

from kpops.components.base_components import KubernetesApp, PipelineComponent, Section
from kpops.components.base_components.kubernetes_app import KubernetesAppValues
from kpops.components.base_components.section import field_order
from kpops.core.registry import Registry

registry = Registry()
registry.discover_components()


class CustomValues(KubernetesAppValues):
    foo: str = "foo"


class CustomApp(KubernetesApp[CustomValues]):
    my_flag: bool = False
    my_name: Annotated[str | None, Section.IDENTITY] = None
    values: CustomValues

    @computed_field
    @property
    def my_derived(self) -> str:
        return "derived"

    @computed_field(alias="myTarget")
    @property
    def my_target(self) -> Annotated[str, Section.TARGET]:
        return "target"

    @computed_field(alias="myAliasedDerived")
    @property
    def my_aliased_derived(self) -> str:
        return "derived"


@pytest.mark.parametrize(
    "component", sorted(registry.components, key=lambda component: component.type)
)
def test_builtin_fields_have_section(component: type[PipelineComponent]) -> None:
    order = field_order(component)
    untagged = [
        name
        for name, field in component.model_fields.items()
        if not field.exclude
        and order[field.serialization_alias or name][0] is Section.CUSTOM
    ]
    assert not untagged


def test_overridden_field_keeps_section() -> None:
    assert field_order(CustomApp)["values"][0] is Section.CONFIG


@pytest.mark.usefixtures("mock_env")
def test_generate_key_order() -> None:
    component = CustomApp(
        name="custom-app",
        namespace="test-namespace",
        values=CustomValues(),
        my_name="my-name",
        my_flag=True,
        extra_b="b",
        extra_a="a",
    )
    assert list(component.generate()) == [
        "type",
        "name",
        "prefix",
        "my_name",
        "enabled",
        "namespace",
        "myTarget",
        "my_flag",
        "values",
        "extra_a",
        "extra_b",
        "my_derived",
        "myAliasedDerived",
    ]
