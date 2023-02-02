from difflib import Differ
from enum import Enum
from typing import Generic, Iterable, Iterator, NamedTuple, Sequence, TypeVar

import typer
import yaml
from dictdiffer import diff, patch

differ = Differ()


class DiffType(str, Enum):
    ADD = "add"
    CHANGE = "change"
    REMOVE = "remove"


T = TypeVar("T")


class Change(NamedTuple, Generic[T]):
    old_value: T
    new_value: T


class Diff(NamedTuple):
    diff_type: DiffType
    key: str
    change: Change


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


def get_diff(d1: dict, d2: dict, ignore: set[str] | None = None) -> Iterator[Diff]:
    for type_of_change, keys, changes in diff(d1, d2, ignore=ignore):
        match type_of_change:
            case DiffType.ADD:
                for key, change in changes:
                    key = __get_key(keys, key)
                    yield Diff(DiffType.ADD, key, Change(None, change))
            case DiffType.REMOVE:
                for key, change in changes:
                    key = __get_key(keys, key)
                    yield Diff(DiffType.REMOVE, key, Change(change, None))
            case DiffType.CHANGE:
                key = __get_key(keys)
                yield Diff(DiffType.CHANGE, key, Change(*changes))


def __get_key(key_1: list | str, key_2: str = "") -> str:
    """
    Generates a string that points to the changed key in the dictionary.
    """
    if isinstance(key_1, list) and len(key_1) > 1:
        return f"{key_1[0]}[{key_1[1]}]"
    if not key_1:
        return key_2
    if not key_2:
        return "".join(key_1)
    return f"{key_1}.{key_2}"


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
