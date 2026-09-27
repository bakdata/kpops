from enum import StrEnum

from typing_extensions import override


class UpperStrEnum(StrEnum):
    @override
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[str]
    ) -> str:
        return name.upper()
