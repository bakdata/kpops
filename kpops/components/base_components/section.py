from collections.abc import Callable, Iterable
from enum import IntEnum, auto
from functools import cache
from typing import Annotated, get_args, get_origin

from pydantic import BaseModel


class Section(IntEnum):
    """Section of a component field, determines the key order in the generated pipeline.

    Assign a field to a section with ``Annotated[T, Section.TARGET]``,
    for computed fields on the return type.
    Within a section, fields of base classes come first, then declaration order.

    :cvar IDENTITY: What the component is called
    :cvar LIFECYCLE: Whether and how the component runs
    :cvar INPUT: Where the component reads from
    :cvar OUTPUT: Where the component writes to
    :cvar TARGET: Where the component is deployed
    :cvar ARTIFACT: What is deployed
    :cvar CUSTOM: Default for fields without a section
    :cvar CONFIG: Configuration of the deployed artifact
    :cvar EXTRA: Undeclared extra fields, sorted alphabetically
    :cvar DERIVED: Default for computed fields without a section
    """

    IDENTITY = auto()
    LIFECYCLE = auto()
    INPUT = auto()
    OUTPUT = auto()
    TARGET = auto()
    ARTIFACT = auto()
    CUSTOM = auto()
    CONFIG = auto()
    EXTRA = auto()
    DERIVED = auto()


def _find_section(metadata: Iterable[object]) -> Section | None:
    return next((item for item in metadata if isinstance(item, Section)), None)


@cache
def field_order(model: type[BaseModel]) -> dict[str, tuple[Section, int]]:
    """Get the sort key of each serialized field of a model.

    Overridden fields keep the section of their parent unless they set their own.

    :param model: Model class
    :returns: Mapping of serialized field name to section and position
    """
    order: dict[str, tuple[Section, int]] = {}

    def register(key: str, section: Section | None, default: Section) -> None:
        if (previous := order.get(key)) is None:
            order[key] = (section or default, len(order))
        elif section is not None:
            order[key] = (section, previous[1])

    for base in reversed(model.__mro__):
        if not issubclass(base, BaseModel):
            continue
        for name, field in base.model_fields.items():
            register(
                field.serialization_alias or name,
                _find_section(field.metadata),
                Section.CUSTOM,
            )
        for name, computed in base.model_computed_fields.items():
            return_type = computed.return_type
            metadata = (
                get_args(return_type)[1:]
                if get_origin(return_type) is Annotated
                else ()
            )
            register(name, _find_section(metadata), Section.DERIVED)
    return order


def section_sort_key(
    model: type[BaseModel],
) -> Callable[[str], tuple[Section, int | str]]:
    """Create a sort key for the serialized field names of a model.

    :param model: Model class
    :returns: Sort key, unknown names are treated as extra fields
    """
    order = field_order(model)

    def key(name: str) -> tuple[Section, int | str]:
        section, position = order.get(name, (Section.EXTRA, 0))
        return section, name if section is Section.EXTRA else position

    return key
