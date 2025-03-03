import re
from collections import ChainMap as _ChainMap
from collections.abc import Mapping
from string import Template
from typing import Any, TypeVar

from typing_extensions import override

_V = TypeVar("_V", bound=object)


def update_nested_pair(
    original_dict: dict[str, _V], other_dict: Mapping[str, _V]
) -> dict[str, _V]:
    """Nested update for 2 dictionaries.

    Adds all new fields in ``other_dict`` to ``original_dict``.
    Does not update existing fields.
    To "update" a dict with new values in existing fields:
    ``original_dict={dict_with_new_values_and_fields}``
    ``other_dict={dict_to_be_updated}``

    :param original_dict: Dictionary to be updated
    :param other_dict: Mapping that contains new key-value pairs
    :return: Updated dictionary
    """
    for key, value in other_dict.items():
        if isinstance(value, Mapping):
            nested_val = original_dict.get(key, {})
            if isinstance(nested_val, dict):
                original_dict[key] = update_nested_pair(nested_val, value)
        elif key not in original_dict:
            original_dict[key] = value
    return original_dict


def update_nested(*argv: dict[str, _V]) -> dict[str, _V]:
    """Merge multiple configuration dicts.

    The dicts have multiple layers. These layers will be merged recursively.

    The leftmost arg has the highest priority, only new fields will be added to it.
    It "updates" the lower prio dict on the right.

    :param argv: n dictionaries
    :returns: Merged configuration dict
    """
    if len(argv) == 0:
        return {}
    if len(argv) == 1:
        return argv[0]
    if len(argv) == 2:
        return update_nested_pair(*argv)
    return update_nested(update_nested_pair(argv[0], argv[1]), *argv[2:])


def flatten_mapping(
    nested_mapping: Mapping[str, _V],
    prefix: str | None = None,
    separator: str = "_",
) -> dict[str, _V]:
    """Flattens a Mapping.

    :param nested_mapping: Nested mapping that is to be flattened
    :param prefix: Prefix that will be applied to all top-level keys in the output., defaults to None
    :param separator: Separator between the prefix and the keys, defaults to "_"
    :returns: "Flattened" mapping in the form of dict
    """
    if not isinstance(nested_mapping, Mapping):
        msg = "Argument nested_mapping is not a Mapping"
        raise TypeError(msg)
    top: dict[str, Any] = {}
    for key, value in nested_mapping.items():
        if not isinstance(key, str):
            msg = f"Argument nested_mapping contains a non-str key: {key}"
            raise TypeError(msg)
        if prefix:
            key = prefix + separator + key
        if isinstance(value, Mapping):
            nested_mapping = flatten_mapping(value, key, separator)  # pyright: ignore[reportAssignmentType,reportUnknownArgumentType]
            top = update_nested_pair(top, nested_mapping)
        else:
            top[key] = value
    return top


def generate_substitution(
    input: dict[str, _V],
    prefix: str | None = None,
    existing_substitution: dict[str, _V] | None = None,
    separator: str | None = None,
) -> dict[str, _V]:
    """Generate a complete substitution dict from a given dict.

    Finds all attributes that belong to a model and expands them to create
    a dict containing each variable name and value to substitute with.

    :param input: Dict from which to generate the substitution
    :param prefix: Prefix the preceeds all substitution variables, defaults to None
    :param substitution: existing substitution to include
    :returns: Substitution dict of all variables related to the model.
    """
    existing_substitution = existing_substitution or {}
    if separator is None:
        return update_nested_pair(existing_substitution, flatten_mapping(input, prefix))
    return update_nested_pair(
        existing_substitution or {}, flatten_mapping(input, prefix, separator)
    )


_sentinel_dict = {}


class ImprovedTemplate(Template):
    """Introduces the dot as an allowed character in placeholders."""

    idpattern = r"(?a:[_a-z][_.a-z0-9]*)"

    @override
    def safe_substitute(self, mapping=_sentinel_dict, /, **kws) -> str:
        if mapping is _sentinel_dict:
            mapping = kws
        elif kws:
            mapping = _ChainMap(kws, mapping)

        # Helper function for .sub()
        def convert(mo: re.Match[str]):
            named = mo.group("named") or mo.group("braced")
            if named is not None:
                try:
                    if "." not in named:
                        return str(mapping[named])
                    return str(mapping[named.replace(".", "__")])
                except KeyError:
                    return mo.group()
            if mo.group("escaped") is not None:
                return self.delimiter
            if mo.group("invalid") is not None:
                return mo.group()
            msg = "Unrecognized named group in pattern"
            raise ValueError(msg, self.pattern)

        return self.pattern.sub(convert, self.template)
