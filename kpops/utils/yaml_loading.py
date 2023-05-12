from collections.abc import Mapping
from pathlib import Path
from string import Template
from typing import Any

import yaml
from cachetools import cached
from cachetools.keys import hashkey


def generate_hashkey(file_path: Path, substitution: dict | None = None) -> tuple:
    if substitution is None:
        substitution = {}
    return hashkey(str(file_path) + str(sorted(substitution.items())))


@cached(cache={}, key=generate_hashkey)
def load_yaml_file(
    file_path: Path, *, substitution: dict | None = None
) -> dict | list[dict]:
    with open(file_path) as yaml_file:
        return yaml.load(substitute(yaml_file.read(), substitution), Loader=yaml.Loader)


def substitute(input: str, substitution: Mapping[str, Any] | None = None) -> str:
    """Substitute $-placeholders in input using template string.

    :param input: The raw input containing $-placeholders
    :type input: str
    :param substitution: The key-value mapping containing substitutions
    :type substitution: Mapping[str, Any] | None
    :return: Substituted input string
    :rtype: str
    """
    if not substitution:
        return input
    return Template(input).safe_substitute(**substitution)


def substitute_nested(input: str, **kwargs) -> str:
    """Allow for multiple substitutions to be passed.

    Will make as many passes as needed to substitute all possible placeholders.

    HINT: If :param input: is a ``Mapping`` that you converted into ``str``,
    You pass it as a string, and as a ``Mapping`` to enable self-reference.

    :Example:

    >>> substitution = {
            "a": "0",
            "b": "${a}",
            "c": "${b}",
            "d": "${a}",
        }
    >>> input = "${a}, ${b}, ${c}, ${d}"
    >>> print("Substituted string: " + substitute_nested(input, **substitution))
    0, 0, 0, 0

    :param input: The raw input containing $-placeholders
    :type input: str
    :param **kwargs: list of Mappings
    :return: Substituted input string
    :rtype: str
    """
    if not {**kwargs}:
        return input
    old_str, new_str = "", substitute(input, {**kwargs})
    while old_str != new_str:
        old_str, new_str = new_str, substitute(new_str, {**kwargs})
    return old_str
