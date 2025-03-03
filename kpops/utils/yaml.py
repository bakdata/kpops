import json
import logging
from collections.abc import Hashable, Mapping
from pathlib import Path
from typing import Any

import yaml
from cachetools import cached
from cachetools.keys import hashkey
from rich.console import Console
from rich.syntax import Syntax

from kpops.utils.dict_ops import ImprovedTemplate

log = logging.getLogger("Yaml")


def generate_hashkey(
    file_path: Path, substitution: Mapping[str, Any] | None = None
) -> tuple[Hashable, ...]:
    if substitution is None:
        substitution = {}
    return hashkey(str(file_path) + str(sorted(substitution.items())))


@cached(cache={}, key=generate_hashkey)
def load_yaml_file(
    file_path: Path, *, substitution: Mapping[str, Any] | None = None
) -> Any:
    log.debug(f"Picked up: {file_path.resolve().relative_to(Path.cwd())}")
    return yaml.safe_load(substitute(file_path.read_text(), substitution))


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


def _diff_substituted_str(s1: str, s2: str):
    """Compare 2 strings, raise exception if not equal.

    :param s1: String to compare
    :param s2: String to compare
    :raises ValueError: An infinite loop condition detected. Check substitution variables.
    """
    if s1 != s2:
        msg = "An infinite loop condition detected. Check substitution variables."
        raise ValueError(msg)


def substitute_nested(input: str, **kwargs: Any) -> str:
    """Allow for multiple substitutions to be passed.

    Will make as many passes as needed to substitute all possible placeholders.

    :Example:

    >>> substitution = {
            "a": "0",
            "b": "${a}",
            "c": "${b}",
            "d": "${a}",
        }
    >>> input = "${a}, ${b}, ${c}, ${d}"
    >>> print("Substituted string: " + substitute_nested(input, **substitution))
    "0, 0, 0, 0"

    :param input: The raw input containing $-placeholders
    :param **kwargs: Substitutions
    :raises ValueError: An infinite loop condition detected. Check substitution variables.
    :return: Substituted input string
    """
    if not kwargs:
        return input
    kwargs = substitute_in_self(kwargs)
    old_str, new_str = "", substitute(input, kwargs)
    steps: set[str] = set()
    while new_str not in steps:
        steps.add(new_str)
        old_str, new_str = new_str, substitute(new_str, kwargs)
    _diff_substituted_str(new_str, old_str)
    return old_str


def substitute_in_self(input: dict[str, Any]) -> dict[str, Any]:
    """Substitute all self-references in mapping.

    Will make as many passes as needed to substitute all possible placeholders.

    :param input: Mapping containing $-placeholders
    :raises ValueError: An infinite loop condition detected. Check substitution variables.
    :return: Substituted input mapping as dict
    """
    old_str, new_str = "", substitute(json.dumps(input), input)
    steps: set[str] = set()
    while new_str not in steps:
        steps.add(new_str)
        old_str, new_str = new_str, substitute(new_str, json.loads(new_str))
    _diff_substituted_str(new_str, old_str)
    return json.loads(old_str)


def multiline_str_representer(
    representer: yaml.representer.SafeRepresenter, data: Any
) -> yaml.ScalarNode:
    if "\n" in data:  # represent multiline strings using block style
        return representer.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return representer.represent_str(data)


yaml.representer.SafeRepresenter.add_representer(str, multiline_str_representer)


class CustomSafeDumper(yaml.SafeDumper):
    def increase_indent(self, flow: bool = False, indentless: bool = False):
        return super().increase_indent(flow, False)


def print_yaml(
    data: Mapping[str, Any] | str, *, substitution: dict[str, Any] | None = None
) -> None:
    """Print YAML object with syntax highlighting.

    :param data: YAML document
    :param substitution: Substitution dictionary, defaults to None
    """
    if not isinstance(data, str):
        data = yaml.dump(dict(data), Dumper=CustomSafeDumper)
        data = f"---\n{data}"
    syntax = Syntax(
        substitute(data, substitution),
        "yaml",
        background_color="default",
        theme="ansi_dark",
    )
    Console(
        width=1000  # HACK: overwrite console width to avoid truncating output
    ).print(syntax)
