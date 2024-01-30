from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from cachetools import cached
from cachetools.keys import hashkey
from rich.console import Console
from rich.syntax import Syntax

from kpops.utils.dict_ops import ImprovedTemplate


def generate_hashkey(
    file_path: Path, substitution: Mapping[str, Any] | None = None
) -> tuple:
    if substitution is None:
        substitution = {}
    return hashkey(str(file_path) + str(sorted(substitution.items())))


@cached(cache={}, key=generate_hashkey)
def load_yaml_file(
    file_path: Path, *, substitution: Mapping[str, Any] | None = None
) -> dict | list[dict]:
    with file_path.open() as yaml_file:
        return yaml.load(substitute(yaml_file.read(), substitution), Loader=yaml.Loader)


def substitute(input: str, substitution: Mapping[str, Any] | None = None) -> str:
    """Substitute `$`-placeholders in input using template string.

    :param input: The raw input containing `$`-placeholders
    :param substitution: The key-value mapping containing substitutions
    :return: Substituted input string
    """
    if not substitution:
        return input

    def prepare_substitution(substitution: Mapping[str, Any]) -> dict[str, Any]:
        """Replace dots with underscores in the substitution keys."""
        return {k.replace(".", "__"): v for k, v in substitution.items()}

    return ImprovedTemplate(input).safe_substitute(**prepare_substitution(substitution))


def substitute_nested(input: str, **kwargs) -> str:
    """Allow for multiple substitutions to be passed.

    Will make as many passes as needed to substitute all possible placeholders.
    A ceiling is set to avoid infinite loops.

    HINT: If :param input: is a ``Mapping`` that you converted into ``str``,
    You can pass it as a string, and as a ``Mapping`` to enable self-reference.

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
    :param **kwargs: Substitutions
    :raises Exception: An infinite loop condition detected. Check substitution variables.
    :return: Substituted input string
    """
    if not kwargs:
        return input
    old_str, new_str = "", substitute(input, kwargs)
    steps = set()
    while new_str not in steps:
        steps.add(new_str)
        old_str, new_str = new_str, substitute(new_str, kwargs)
    if new_str != old_str:
        msg = "An infinite loop condition detected. Check substitution variables."
        raise ValueError(msg)
    return old_str


def print_yaml(data: Mapping | str, *, substitution: dict | None = None) -> None:
    """Print YAML object with syntax highlighting.

    :param data: YAML document
    :param substitution: Substitution dictionary, defaults to None
    """
    if not isinstance(data, str):
        data = yaml.safe_dump(dict(data))
    syntax = Syntax(
        substitute(data, substitution),
        "yaml",
        background_color="default",
        theme="ansi_dark",
    )
    Console(
        width=1000  # HACK: overwrite console width to avoid truncating output
    ).print(syntax)
