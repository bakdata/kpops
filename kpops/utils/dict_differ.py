from __future__ import annotations

from dataclasses import dataclass
from difflib import Differ
from enum import Enum
from typing import TYPE_CHECKING, Generic, TypeVar

import typer
import yaml
from dictdiffer import diff, patch

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

differ = Differ()


class DiffType(str, Enum):
    ADD = "add"
    CHANGE = "change"
    REMOVE = "remove"

    @staticmethod
    def from_str(label: str) -> DiffType:
        return DiffType[label.upper()]


T = TypeVar("T")


@dataclass
class Change(Generic[T]):  # Generic NamedTuple requires Python 3.11+
    old_value: T
    new_value: T

    @staticmethod
    def factory(type: DiffType, change: T | tuple[T, T]) -> Change:
        match type:
            case DiffType.ADD:
                return Change(None, change)
            case DiffType.REMOVE:
                return Change(change, None)
            case DiffType.CHANGE if isinstance(change, tuple):
                return Change(*change)
        msg = f"{type} is not part of {DiffType}"
        raise ValueError(msg)


@dataclass
class Diff(Generic[T]):
    diff_type: DiffType
    key: str
    change: Change[T]

    @staticmethod
    def from_dicts(
        d1: dict, d2: dict, ignore: set[str] | None = None
    ) -> Iterator[Diff]:
        for diff_type, keys, changes in diff(d1, d2, ignore=ignore):
            if not isinstance(changes_tmp := changes, list):
                changes_tmp = [("", changes)]
            for key, change in changes_tmp:
                yield Diff(
                    DiffType.from_str(diff_type),
                    Diff.__find_changed_key(keys, key),
                    Change.factory(diff_type, change),
                )

    @staticmethod
    def __find_changed_key(key_1: list[str] | str, key_2: str = "") -> str:
        """Generate a string that points to the changed key in the dictionary."""
        if isinstance(key_1, list) and len(key_1) > 1:
            return f"{key_1[0]}[{key_1[1]}]"
        if not key_1:
            return key_2
        if not key_2:
            return "".join(key_1)
        return f"{key_1}.{key_2}"


def render_diff(d1: dict, d2: dict, ignore: set[str] | None = None) -> str | None:
    differences = list(diff(d1, d2, ignore=ignore))
    if not differences:
        return None

    d2_filtered: dict = patch(differences, d1)
    return "".join(
        colorize_diff(
            differ.compare(
                to_yaml(d1) if d1 else "",
                to_yaml(d2_filtered) if d2_filtered else "",
            )
        )
    )


def colorize_diff(input: Iterable[str]) -> Iterator[str]:
    for line in input:
        yield colorize_line(line)


def colorize_line(line: str) -> str:
    if line.startswith("-"):
        return typer.style(line, fg=typer.colors.RED)
    if line.startswith("+"):
        return typer.style(line, fg=typer.colors.GREEN)
    if line.startswith("?"):
        return typer.style(line, fg=typer.colors.YELLOW)
    return line


def to_yaml(data: dict) -> Sequence[str]:
    return yaml.dump(data, sort_keys=True).splitlines(keepends=True)
