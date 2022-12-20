from difflib import Differ
from enum import Enum
from typing import Any, Iterable, Iterator, Sequence

import typer
import yaml
from dictdiffer import diff, patch
from pydantic import BaseModel

differ = Differ()


class DiffType(str, Enum):
    ADD = "add"
    CHANGE = "change"
    REMOVE = "remove"


class Change(BaseModel):
    old_value: Any | None
    new_value: Any | None


class Diff(BaseModel):
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


def get_diff(d1: dict, d2: dict, ignore: set[str] | None = None) -> list[Diff]:
    differences = list(diff(d1, d2, ignore=ignore))
    diff_list = []
    for difference in differences:
        if difference[0] == DiffType.ADD.value:
            for key, change in difference[2]:
                diff_object = Diff(
                    diff_type=DiffType[difference[0].upper()],
                    key=__get_key(difference[1], key),
                    change=Change(old_value=None, new_value=change),
                )
                diff_list.append(diff_object)

        elif difference[0] == DiffType.REMOVE.value:
            for key, change in difference[2]:
                diff_object = Diff(
                    diff_type=DiffType[difference[0].upper()],
                    key=__get_key(difference[1], key),
                    change=Change(old_value=change, new_value=None),
                )
                diff_list.append(diff_object)

        elif difference[0] == DiffType.CHANGE.value:
            diff_object = Diff(
                diff_type=DiffType[difference[0].upper()],
                key=__get_key(difference[1], ""),
                change=Change(old_value=difference[2][0], new_value=difference[2][1]),
            )
            diff_list.append(diff_object)
        else:
            raise ValueError(
                f"Unsupported diff type of {difference[0]}. Suppoerted diff types are: ADD, CHANGE, REMOVE."
            )

    return diff_list


def __get_key(key_1: list[Any] | str, key_2: str) -> str:
    """
    Generates a string that points to the changed key in the dictionary.
    """
    if len(key_1) > 1 and type(key_1) == list:
        return f"{key_1[0]}[{key_1[1]}]"
    else:
        if key_1 == "":
            return key_2
        elif key_2 == "":
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
