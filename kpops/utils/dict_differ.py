from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from difflib import Differ
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Generic, NamedTuple, TypeVar, cast

import typer
import yaml
from dictdiffer import diff, patch

from kpops.component_handlers.helm_wrapper.model import KeyPath

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

differ = Differ()


class DiffType(StrEnum):
    ADD = "add"
    CHANGE = "change"
    REMOVE = "remove"

    @staticmethod
    def from_str(label: str) -> DiffType:
        return DiffType[label.upper()]


_O = TypeVar("_O")
_N = TypeVar("_N")


class Change(NamedTuple, Generic[_O, _N]):
    old_value: _O
    new_value: _N

    @staticmethod
    def factory(
        type: DiffType, change: _O | _N | tuple[_O, _N]
    ) -> Change[_O | None, _N | None]:
        match type:
            case DiffType.ADD:
                change = cast(_N, change)
                return Change(None, change)
            case DiffType.REMOVE:
                change = cast(_O, change)
                return Change(change, None)
            case DiffType.CHANGE:
                change = cast(tuple[_O, _N], change)
                return Change(*change)
        msg = f"{type} is not part of {DiffType}"  # pyright: ignore[reportUnreachable]
        raise ValueError(msg)


@dataclass
class Diff(Generic[_O, _N]):
    diff_type: DiffType
    key: str
    change: Change[_O, _N]

    @staticmethod
    def from_dicts(
        d1: dict[str, Any], d2: dict[str, Any], ignore: set[str] | None = None
    ) -> Iterator[Diff[Any, Any]]:
        for diff_type, keys, changes in diff(d1, d2, ignore=ignore):
            diff_type = DiffType.from_str(diff_type)  # pyright: ignore[reportUnknownArgumentType]
            if not isinstance(changes_tmp := changes, list):
                changes_tmp: list[tuple[str, Any]] = [("", changes)]
            for key, change in changes_tmp:
                yield Diff(
                    diff_type,
                    Diff.__find_changed_key(keys, key),  # pyright: ignore[reportUnknownArgumentType]
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


def render_diff(
    d1: MutableMapping[str, Any],
    d2: MutableMapping[str, Any],
    ignore: list[KeyPath] | None = None,
) -> str | None:
    def del_ignored_keys(d: MutableMapping[str, Any]) -> None:
        """Delete key to be ignored, dictionary is modified in-place."""
        if ignore:
            for key_path in ignore:
                nested = d
                try:
                    for key in key_path[:-1]:
                        nested = nested[key]
                    del nested[key_path[-1]]
                except KeyError:
                    continue

    del_ignored_keys(d1)
    del_ignored_keys(d2)

    differences = list(diff(d1, d2))
    if not differences:
        return None

    d2_filtered: Mapping[str, Any] = patch(differences, d1)
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


def to_yaml(data: Mapping[str, Any]) -> Sequence[str]:
    return yaml.safe_dump(data, sort_keys=True).splitlines(keepends=True)
