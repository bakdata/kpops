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
        return load_yaml(yaml_file.read(), substitution=substitution)


def load_yaml(content: str, *, substitution: dict | None = None) -> dict | list[dict]:
    return yaml.load(substitute(content, substitution), Loader=yaml.Loader)


def substitute(input: str, substitution: Mapping[str, Any] | None = None) -> str:
    """
    Substitute $-placeholders in input using template string.
    :param input: The raw input containing $-placeholders
    :param substitution: The key-value mapping containing substitutions
    :return: Substituted input string
    """
    if not substitution:
        return input
    return Template(input).safe_substitute(**substitution)
